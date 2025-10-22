import re
from urllib.parse import urljoin
from typing import Any, Dict, List, Tuple

import aiohttp
import bs4
from bs4 import BeautifulSoup
import requests

from utils.bs4 import extract_strings
from errors import DataParseError
from config.constants import COMMON_HEADERS
from ..__init__ import domain, base_url


def _get_arguments(path: str) -> Dict[str, str]:
    """
    返回网络请求的必要参数。

    Params:

    - path: 老师的个人页面的链接，要被连接到 `base_url` 后面，如 `"/Data/View/3967"`。
    """
    headers = COMMON_HEADERS | {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    return {
        "url": urljoin(base_url, path),
        "headers": headers,
        # "verify": False,
    }


def view(path: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - path: 老师的个人页面的链接，要被连接到 `base_url` 后面，如 `"/Data/View/3967"`。
    - kwargs: 传递给 requests.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/鲍峰.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(path)
    response = requests.get(**arguments)
    return parse_data(response.text)


async def async_view(path: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - path: 老师的个人页面的链接，要被连接到 `base_url` 后面，如 `"/Data/View/3967"`。
    - kwargs: 传递给 aiohttp.ClientSession.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/鲍峰.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return parse_data(await response.text())


def _extract_teach_title(title_tag: bs4.Tag | None) -> str:
    """
    从结构为

    ```html
    <div class="teach-title">
        <span style="color:333;font-size:18px">鲍峰</span>
    </div>
    ```

    的 Tag 对象 `title_tag` 中提取数据。

    Return like:

    ```python
    "鲍峰"
    ```
    """
    if not title_tag:
        return ""
    name_tag = title_tag.find("span")
    return name_tag.get_text(strip = True) if name_tag else ""


def _extract_teach_intro(intro_tag: bs4.Tag | None) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="teach-intro">
        <p class="title">
            <img src="/Assets/images/1.png" style="width:11px;" />
            通信科学与工程系
        </p>
        <p>
            <img src="/Assets/images/8.png" />
            职称：青年研究员
        </p>
        <p>
            <img src="/Assets/images/wen.png" style="width:15px;margin-right:6px;" />
            职务：无
        </p>
        <p>
            <img src="/Assets/images/2.png" />
            电子邮件：fbao@fudan.edu.cn
        </p>
        <p>
            <img src="/Assets/images/3.png" />
            办公地点：邯郸校区遗传学楼
        </p>
        <p>
            <img src="/Assets/images/4.png" />
            电话：
        </p>
        <p>
            <img src="/Assets/images/6.png" />
            课题组主页：
            <a target="_blank" href="https://fbao-fudan.github.io/">https://fbao-fudan.github.io/</a>
        </p>
    </div>
    ```

    的 Tag 对象 `intro_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        "院系": "通信科学与工程系",

        # 可能有的字段
        "职称": "青年研究员",
        "职务": "无",
        "电子邮件": "fbao@fudan.edu.cn",
        "办公地点": "邯郸校区遗传学楼",
        "电话": "",
        "课题组主页": "https://fbao-fudan.github.io/",
    }
    ```
    """
    result = {"院系": ""}
    if not intro_tag:
        return result

    # 院系
    department_tag = intro_tag.find("p", class_ = "title")
    department = department_tag.get_text(strip = True) if department_tag else ""
    result["院系"] = department

    # 其他
    for sub_tag in intro_tag.children:
        if "：" in sub_tag.get_text():
            (key, value) = sub_tag.get_text(strip = True).split("：", 1)
            result[key] = value

    return result


def _extract_teach_left(left_tag: bs4.Tag) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="teach-left">
        <div class="teach-title">
            <span style="color:333;font-size:18px">鲍峰</span>
        </div>
        <div class="teach-intro">
            <p class="title"><img src="/Assets/images/1.png" style="width:11px;" />通信科学与工程系</p>
            <p><img src="/Assets/images/8.png" />职称：青年研究员</p>
            <p><img src="/Assets/images/wen.png" style="width:15px;margin-right:6px;" />职务：无</p>
            <p><img src="/Assets/images/2.png" />电子邮件：fbao@fudan.edu.cn</p>
            <p><img src="/Assets/images/3.png" />办公地点：邯郸校区遗传学楼</p>
            <p><img src="/Assets/images/4.png" />电话：</p>
            <p><img src="/Assets/images/6.png" />课题组主页：<a target="_blank" href="https://fbao-fudan.github.io/">https://fbao-fudan.github.io/</a></p>
        </div>
    </div>
    ```

    的 Tag 对象 `left_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        "姓名": "鲍峰",
        "院系": "通信科学与工程系",

        # 可能有的字段
        "职称": "青年研究员",
        "职务": "无",
        "电子邮件": "fbao@fudan.edu.cn",
        "办公地点": "邯郸校区遗传学楼",
        "电话": "",
        "课题组主页": "https://fbao-fudan.github.io/",
    }
    ```
    """
    title_tag = left_tag.find("div", class_ = "teach-title")
    name = _extract_teach_title(title_tag)

    intro_tag = left_tag.find("div", class_ = "teach-intro")
    intro_data = _extract_teach_intro(intro_tag)

    return {
        "姓名": name
    } | intro_data


def _extract_teach_right(right_tag: bs4.Tag) -> str:
    """
    从结构为

    ```html
    <div class="teach-right">
        <img src="/assets/userfiles/images/Net/20250918/20250918/6389380754716414812723197.png" width="162" height="200" />
    </div>
    ```

    的 Tag 对象 `right_tag` 中提取数据。

    Return like:

    ```python
    "/assets/userfiles/images/Net/20250918/20250918/6389380754716414812723197.png"
    ```
    """
    img_tag = right_tag.find("img", attrs={'src': True})
    return img_tag.get('src') if img_tag else ""


def _extract_teach_info(info_tag: bs4.Tag) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="teach-info">
        <div class="teach-left">
            <div class="teach-title">
                <span style="color:333;font-size:18px">鲍峰</span>
            </div>
            <div class="teach-intro">
                <p class="title"><img src="/Assets/images/1.png" style="width:11px;" />通信科学与工程系</p>
                <p><img src="/Assets/images/8.png" />职称：青年研究员</p>
                <p><img src="/Assets/images/wen.png" style="width:15px;margin-right:6px;" />职务：无</p>
                <p><img src="/Assets/images/2.png" />电子邮件：fbao@fudan.edu.cn</p>
                <p><img src="/Assets/images/3.png" />办公地点：邯郸校区遗传学楼</p>
                <p><img src="/Assets/images/4.png" />电话：</p>
                <p><img src="/Assets/images/6.png" />课题组主页：<a target="_blank" href="https://fbao-fudan.github.io/">https://fbao-fudan.github.io/</a></p>
            </div>
        </div>
        <div class="teach-right">
            <img src="/assets/userfiles/images/Net/20250918/20250918/6389380754716414812723197.png" width="162" height="200" />
        </div>
    </div>
    ```

    的 Tag 对象 `info_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        "姓名": "鲍峰",
        "院系": "通信科学与工程系",
        "头像": "/assets/userfiles/images/Net/20250918/20250918/6389380754716414812723197.png"

        # 可能有的字段
        "职称": "青年研究员",
        "职务": "无",
        "电子邮件": "fbao@fudan.edu.cn",
        "办公地点": "邯郸校区遗传学楼",
        "电话": "",
        "课题组主页": "https://fbao-fudan.github.io/",
    }
    ```
    """
    left_tag = info_tag.find("div", class_ = "teach-left")
    info = _extract_teach_left(left_tag)

    right_tag = info_tag.find("div", class_ = "teach-right")
    img_url = _extract_teach_right(right_tag)
    info["头像"] = img_url

    return info


def _extract_teach_nav(navigation_tag: bs4.Tag | None) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="teach-nav">
        <ul>
            <li><a class="active" href="javascript:;" data-id="1">研究兴趣</a></li>
            <li><a href="javascript:;" data-id="2">学术任职</a></li>
            <li><a href="javascript:;" data-id="3">获奖情况</a></li>
            <li><a href="javascript:;" data-id="4">学习工作经历</a></li>
            <li><a href="javascript:;" data-id="5">授课情况</a></li>
            <li><a href="javascript:;" data-id="6">代表性论文或专著</a></li>
        </ul>
    </div>
    ```

    的 Tag 对象 `navigation_tag` 中提取数据。

    Return like:

    ```python
    {
        # 可能有的字段
        "研究兴趣": "1",
        "学术任职": "2",
        "获奖情况": "3",
        "学习工作经历": "4",
        "授课情况": "5",
        "代表性论文或专著": "6",
    }
    ```
    """
    result = {}

    if not navigation_tag:
        return result

    ul_tag = navigation_tag.find("ul")
    if not ul_tag:
        return result

    for li_tag in ul_tag.find_all("li"):
        a_tag = li_tag.find("a")
        result[a_tag.get_text(strip = True)] = a_tag.get("data-id")

    return result


def _extract_tab(tab_tag: bs4.Tag | None) -> str:
    r"""
    从结构为

    ```html
    <div id="tab_1" class="tabcss">
        <p><strong>人工智能方法：</strong></p>
        <p>(1) 自监督表示学习方法。</p>
        <p>(2) 多模态信息融合方法。</p>
        <p>(3) 因果关系推理方法。</p>

        <p><strong>AI for Science：</strong></p>
        <p>(1) 生命科学：设计大规模、多模态的人工智能方法，应用于单细胞组学、空间组学、多模态生物数据，为生命科学研究提供由浅入深的解析工具，服务脑科学、肿瘤、衰老等问题研究。</p>
        <p>(2) 药物科学：结合表型药物筛选显微平台（High-content image-based phenotypic screen），设计跨细胞系、显微平台、药物库的大规模药物筛选方法，加速小分子药物发现。</p>
        <p>(3) 自然科学：设计针对全球长时程观测数据的人工智能方法，探索在气象、城市、环境的科学价值。</p>

        <p><strong>实验室招聘研究助理。</strong>欢迎博士后合作，直博生、普博生、<strong>硕士生</strong>报考，本科生科研实践，近期特别关注方向：<span style="background-color: orange">空间组学，肿瘤科学与自然科学的AI方法</span>。请联系 fbao@fudan.edu.cn。</p>
    </div>
    ```

    的 Tag 对象 `tab_tag` 中提取数据。

    Return like:

    ```python
    "人工智能方法：\n(1) 自监督表示学习方法。\n(2) 多模态信息融合方法。\n(3) 因果关系推理方法。\nAI for Science：\n(1) 生命科学：设计大规模、多模态的人工智能方法，应用于单细胞组学、空间组学、多模态生物数据，为生命科学研究提供由浅入深的解析工具，服务脑科学、肿瘤、衰老等问题研究。\n(2) 药物科学：结合表型药物筛选显微平台（High-content image-based phenotypic screen），设计跨细胞系、显微平台、药物库的大规模药物筛选方法，加速小分子药物发现。\n(3) 自然科学：设计针对全球长时程观测数据的人工智能方法，探索在气象、城市、环境的科学价值。\n实验室招聘研究助理。欢迎博士后合作，直博生、普博生、硕士生报考，本科生科研实践，近期特别关注方向：空间组学，肿瘤科学与自然科学的AI方法。联系 fbao@fudan.edu.cn。"
    ```
    """
    if not tab_tag:
        return ""
    contents: List[str] = []
    for sub_tag in tab_tag.children:
        content = ""
        if sub_tag.name == "p":
            content = "".join(extract_strings(sub_tag))
        elif sub_tag.name == "ul":
            texts = []
            for li in sub_tag.find_all("li"):
                text = ''.join(extract_strings(li)).strip()
                if text:
                    texts.append(text)
            content = "\n".join(f"- {text}" for text in texts)
        elif sub_tag.name == "ol":
            texts = []
            for li in sub_tag.find_all("li"):
                text = ''.join(extract_strings(li)).strip()
                if text:
                    texts.append(text)
            content = "\n".join(f"- {text}" for text in texts)
        contents.append(content)
    return "\n".join(contents)


def _extract_team(team_tag: bs4.Tag) -> Dict[str, str]:
    r"""
    从结构为

    ```html
    <div class="team">
        <div class="teach-info">
            <div class="teach-left">
                <div class="teach-title">...</div>
                <div class="teach-intro">...</div>
            </div>
            <div class="teach-right">...</div>
            <div class="clearfix">...</div>
        </div>
        <div class="teach-nav">...</div>
        <div id="tab_1" class="tabcss" style="display: none;">...</div>
        <div id="tab_2" class="tabcss" style="display: none;">...</div>
        <div id="tab_3" class="tabcss" style="display: none;">...</div>
        <div id="tab_4" class="tabcss" style>...</div>
        <div id="tab_5" class="tabcss" style="display: none;">...</div>
        <div id="tab_6" class="tabcss" style="display: none;">...</div>
    </div>
    ```

    的 Tag 对象 `team_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        '姓名': '鲍峰',
        '职称': '青年研究员',
        '头像': '/assets/userfiles/images/Net/20250918/20250918/6389380754716414812723197.png',

        # 可能有的字段
        '院系': '通信科学与工程系',
        '职务': '无',
        '电子邮件': 'fbao@fudan.edu.cn',
        '办公地点': '邯郸校区遗传学楼',
        '电话': '',
        '课题组主页': 'https://fbao-fudan.github.io/',
        '研究兴趣': '人工智能方法:\n(1)   自监督表示学习方法。\n(2)   多模态信息融合方法。\n(3)   因果关系推理方法。\n \nAI for Science:\n(1)   生命科学：设计大规模、多模态的人工智能方法，应用于单细胞组学、空间组学、多模态生物数据，为生命科学研究提供由浅入深的解析工具，服务脑科学、肿瘤、衰老等问题研究。\n(2)   药物科学：结合表型药物筛选显微平台（High-content image-based phenotypic screen），设计跨细胞系、显微平台、药物库的大规模药物筛选方法，加速小分子药物发现。\n(3)   自然科学：设计针对全球长时程观测数据的人工智能方法，探索在气象、城市、环境的科学价值。\n\n实验室招聘研究助理。欢迎博士后合作，直博生、普博生、硕士生报考，本科生科研实践，近期特别关注方向：空间组学，肿瘤科学与自然科学的AI方法。请联系 fbao@fudan.edu.cn。',
        '学术任职': '编委：\nThe Innovation Medicine\n编辑：\nPLOS Computational Biology Guest editor\n\n学术期刊审稿人:\n- Cell\n- Nature Biotechnology\n- Nature Communications\n- Cell Systems\n- Genome Biology\n- IEEE Transactions on Fuzzy Systems\n- IEEE Transactions on Neural Networks and Learning Systems\n- Briefings in Bioinformatics\n- IEEE Journal of Selected Topics in Signal Processing',
        '获奖情况': '2023 国家高层次青年人才\n2023 上海市高层次青年人才\n2021 Cell Press中国最受欢迎文章\n2021 Germany DAAD AInet Fellowship\n2021 CICAI International Conference on Artificial Intelligence, Best Paper finalist\n2020 IEEE CIS Transactions on Fuzzy Systems Outstanding Paper Award\n2020 世界人工智能大会杰出青年论文奖.\n2019 北京市优秀博士学位论文\n2019 清华大学优秀博士学位论文',
        '学习工作经历': '复旦大学 / 信息科学与工程学院\n青年研究员\n2024年11月 – 今\n \n加州大学旧金山分校 / 药物化学系\n博士后\n2019年11月 – 2024年9月\n\n清华大学 / 自动化系\n工学博士\n2014年9月 – 2019年7月\n \n哈佛大学 Dana-Farber 癌症研究中心 / 数据科学系\n访问学者\n2018年3月 – 2019年1月\n\n\n西安电子科技大学 / 电子信息工程\n工学学士\n2010年9月 – 2014年7月',
        '授课情况': '2025春季学期《前沿讲座》（与迟楠老师合作）\n2025秋季学期《人工智能基础》AIB210002.07',
        '代表性论文或专著': '一作/通讯代表性文章：\n\n1.    Transitive prediction of small molecule function through alignment of high-content screening resources.Nature Biotechnology. 2025. doi: https://doi.org/10.1038/s41587-025-02729-2.\n2.    Tissue characterization at an enhanced resolution across spatial omics platforms with deep generative model.Nature Communications. 2024, 15(1): 6541.\n3.    Integrative spatial analysis of cell morphologies and transcriptional states with MUSE.Nature Biotechnology. 2022, 1-10.\n4.    Explaining the Genetic Causality for Complex Phenotype via Deep Association Kernel Learning.Patterns, Cell Press. 2020, 100057. (封面文章)\n5.    Scalable analysis of cell type composition from single-cell transcriptomics using deep recurrent learning.Nature Methods. 2019, 16: 311–314.'
    }
    ```
    """
    info_tag = team_tag.find("div", class_ = "teach-info")
    info = _extract_teach_info(info_tag)

    nav_tag = team_tag.find("div", class_ = "teach-nav")
    navigation = _extract_teach_nav(nav_tag)

    for (field, data_id) in navigation.items():
        tab_tag = team_tag.find("div", id = f"tab_{data_id}")
        info[field] = _extract_tab(tab_tag).replace("\xa0", " ").strip()

    return info


def parse_data(text: str) -> Dict[str, str]:
    r"""
    从响应的文本中提取数据。

    Params:

    - text: view() 或 async_view() 返回的结果。

    Return like: 见 _extract_team()
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    soup = BeautifulSoup(text, 'html.parser')

    team_tag = soup.find("div", class_ = "team")

    return _extract_team(team_tag)
