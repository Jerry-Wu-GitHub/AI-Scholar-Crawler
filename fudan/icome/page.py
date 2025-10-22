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
from .__init__ import domain, base_url


def _get_arguments(path: str) -> Dict[str, str]:
    """
    返回网络请求的必要参数。

    Params:

    - path: 老师的个人页面的链接，要被连接到 `base_url` 后面，如 `"/21/ac/c49294a729516/page.htm"`。
    """
    headers = COMMON_HEADERS | {
        'authority': domain,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'cache-control': 'max-age=0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
    }

    return {
        "url": urljoin(base_url, path),
        "headers": headers,
    }


def page(path: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - path: 老师的个人页面的链接，要被连接到 `base_url` 后面，如 `"/21/ac/c49294a729516/page.htm"`。
    - kwargs: 传递给 requests.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/步文博.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(path)
    response = requests.get(**arguments)
    return parse_data(response.text)


async def async_page(path: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - path: 老师的个人页面的链接，要被连接到 `base_url` 后面，如 `"/21/ac/c49294a729516/page.htm"`。
    - kwargs: 传递给 aiohttp.ClientSession.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/步文博.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return parse_data(await response.text())


def _extract_person_tt(title_tag: bs4.Tag | None) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="person-tt fl">
        <p class="p1">步文博</p>
        <p>教授</p>
        <p>电话：021-31243520</p>
        <p>邮箱：wbbu@fudan.edu.cn</p>
        <p>办公地点：复旦大学（江湾校区）化学楼B6075室</p>
        <p>课题组主页：http://faculty.fudan.edu.cn/buwenbo/zh_CN/index.htm</p>
    </div>
    ```

    的 Tag 对象 `title_tag` 中提取数据。

    Return like:

        {
            "姓名": "步文博",
            "职称": "教授",
            "电话": "021-31243520",
            "邮箱": "wbbu@fudan.edu.cn",
            "办公地点": "复旦大学（江湾校区）化学楼B6075室",
            "课题组主页": "http://faculty.fudan.edu.cn/buwenbo/zh_CN/index.htm",
        }
    """
    pairs: List[List[str]] = []

    # 姓名
    name = title_tag.find('p', class_='p1').get_text(strip = True) if title_tag else ""
    pairs.append(["姓名", name])

    # 职称
    academic_title = ""
    if title_tag and len(title_tag.contents) > 1:
        academic_title = title_tag.contents[1].get_text(strip = True)
    pairs.append(["职称", academic_title])

    # 其他字段
    for p in title_tag.contents[2:]:
        text = p.get_text(strip = True)
        if "：" in text:
            pairs.append([s.strip() for s in text.split("：", 1)])

    return dict(pairs)


def _extract_person_top(top_tag: bs4.Tag | None) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="person-top">
        <div class="person-img fl">
            <img src="/_upload/article/images/4c/97/1fea7d1940d58eb0f447863bef41/54ae1324-0c3e-448b-8a8b-8dddd2c91918.png">
        </div>
        <div class="person-tt fl">
            <p class="p1">步文博</p>
            <p>教授</p>
            <p>电话：021-31243520</p>
            <p>邮箱：wbbu@fudan.edu.cn</p>
            <p>办公地点：复旦大学（江湾校区）化学楼B6075室</p>
            <p>课题组主页：http://faculty.fudan.edu.cn/buwenbo/zh_CN/index.htm</p>
        </div>
        <div class="clearfix">
        </div>
    </div>
    ```

    的 Tag 对象 `top_tag` 中提取数据。

    Return like:

    ```python
    {
        "头像": "/_upload/article/images/4c/97/1fea7d1940d58eb0f447863bef41/54ae1324-0c3e-448b-8a8b-8dddd2c91918.png",
        "姓名": "步文博",
        "职称": "教授",
        "电话": "021-31243520",
        "邮箱": "wbbu@fudan.edu.cn",
        "办公地点": "复旦大学（江湾校区）化学楼B6075室",
        "课题组主页": "http://faculty.fudan.edu.cn/buwenbo/zh_CN/index.htm",
    }
    ```
    """

    img_div = top_tag.find("div", class_ = "person-img")
    img_tag = img_div.find("img", attrs={'src': True}) if img_div else None
    img_url = img_tag.get("src", default = "") if img_tag else ""

    title_tag = top_tag.find('div', class_='person-tt')

    return {
        "头像": img_url
    } | _extract_person_tt(title_tag)


def _extract_person_dcon(dcon_tag: bs4.Tag | None) -> Tuple[str, List[str]]:
    """
    从结构为

    ```html
    <div class="person-dcon">
        <h4>主要荣誉和奖励</h4>
        <ul class="w-ul-disc list-paddingleft-2">
            <li>
                <p>课题组PI步文博教授，曾获得国家杰出青年科学基金（结题评价：优秀A）、科技部中青年科技创新领军人才、上海市优秀学术带头人等人才计划。</p>
            </li>
            <li>
                <p>2022年，荣获上海市自然科学奖一等奖（第一完成人：步文博）<br></p>
            </li>
            <li>
                <p>2022年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家</p>
            </li>
            <li>
                <p>2021年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家</p>
            </li>
            <li>
                <p>2020年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家</p>
            </li>
            <li>
                <p>2019年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家</p>
            </li>
            <li>
                <p>2017年，入选“国家自然科学基金委杰出青年科学基金”</p>
            </li>
            <li>
                <p>2017年，入选科技部“中青年科技创新领军人才计划”</p>
            </li>
            <li>
                <p>2016年，入选“上海市优秀学术带头人计划”2012年，入选“上海市青年科技启明星跟踪计划”</p>
            </li>
            <li>
                <p>2012年，入选“上海市人才发展资金计划”</p>
            </li>
            <li>
                <p>2012年，获“中国科学院上海分院第三届杰出青年科技创新人才提名奖”</p>
            </li>
            <li>
                <p>2008年，获“第五届柳大纲优秀青年科技奖”</p>
            </li>
            <li>
                <p>2007年，入选“上海市青年科技启明星计划（A类）”</p>
            </li>
            <li>
                <p>2004年，获“国防科学技术二等奖”（排名第三）</p>
            </li>
        </ul>
    </div>
    ```

    的 Tag 对象 `dcon_tag` 中提取数据。

    Return like:

    ```python
    (
        "主要荣誉和奖励",
        [
            "课题组PI步文博教授，曾获得国家杰出青年科学基金（结题评价：优秀A）、科技部中青年科技创新领军人才、上海市优秀学术带头人等人才计划。",
            "2022年，荣获上海市自然科学奖一等奖（第一完成人：步文博）",
            "2022年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家",
            "2021年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家",
            "2020年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家",
            "2019年，入选 Clarivate Analytics（科睿唯安）全球高被引科学家",
            "2017年，入选“国家自然科学基金委杰出青年科学基金”",
            "2017年，入选科技部“中青年科技创新领军人才计划”",
            "2016年，入选“上海市优秀学术带头人计划”2012年，入选“上海市青年科技启明星跟踪计划”",
            "2012年，入选“上海市人才发展资金计划”",
            "2012年，获“中国科学院上海分院第三届杰出青年科技创新人才提名奖”",
            "2008年，获“第五届柳大纲优秀青年科技奖”",
            "2007年，入选“上海市青年科技启明星计划（A类）”",
            "2004年，获“国防科学技术二等奖”（排名第三）",
        ]
    )
    ```
    """

    h4_tag = dcon_tag.find("h4")
    heading = h4_tag.get_text(strip = True) if h4_tag else ""

    contents: List[str] = []
    for sub_tag in dcon_tag.contents[1:]:
        contents.extend(extract_strings(sub_tag))

    return (heading, contents)


def _extract_person_con(con_tag: bs4.Tag, sep: str = '\n') -> Dict[str, str]:
    r"""
    从结构为

    ```html
    <div class="person-con">
      <div class="person-dcon">
        <h4>教育和工作经历</h4>
        <ul>
          <li>2025/04-　复旦大学智能材料与未来能源创新学院　教授/博导</li>
          <li>2020/03-2025/04　复旦大学材料科学系　教授/博导</li>
          <li>2016/03-2020/02　华东师大化学与分子工程学院　教授/博导</li>
          <li>2008/09-2016/02　中科院上海硅酸盐所　研究员/博导</li>
          <li>2002/08-2008/08　同所　博士后→助研→副研</li>
          <li>1997/09-2002/06　南京工业大学　材料学　博士</li>
          <li>1993/09-1997/07　齐鲁工业大学　材料学　学士</li>
        </ul>
      </div>

      <div class="person-dcon">
        <h4>研究方向</h4>
        <p>材料生物学（无机生物化学与医用功能材料）</p>
        <ol>
          <li>光/电/磁功能材料的合成方法学</li>
          <li>稀土功能材料：光磁学、分子影像、肿瘤诊疗</li>
          <li>功能材料用于脑科学（神经显像与调控）</li>
        </ol>
        <p>常年招收材料、化学、物理、生物、基础医学等背景研究生与博士后。</p>
      </div>

      <div class="person-dcon">
        <h4>主讲课程</h4>
        <ul><li>《生命、医学与材料》</li></ul>
      </div>

      <div class="person-dcon">
        <h4>主要荣誉和奖励</h4>
        <ul>
          <li>国家杰青（结题优秀A）</li>
          <li>科技部中青年科技创新领军人才</li>
          <li>上海市自然科学一等奖（2022，第一完成人）</li>
          <li>Clarivate全球高被引科学家（2019-2022连续）</li>
          <li>上海市优秀学术带头人等</li>
        </ul>
      </div>

      <div class="person-dcon">
        <h4>项目合作单位</h4>
        <ul>
          <li>复旦：肿瘤、华山、华东医院</li>
          <li>上海交大新华医院、同济十院</li>
          <li>海军军医大长海/长征医院</li>
          <li>NUS、U Queensland、UTS 等</li>
        </ul>
      </div>

      <div class="person-dcon">
        <h4>学术组织兼职</h4>
        <p>中国生物材料学会理事、影像材料分会候任主委；BMEMat 副主编；Chem. Soc. Rev./Bioconjugate Chem. 等期刊编委。</p>
      </div>

      <div class="person-dcon">
        <h4>近5年代表性论著</h4>
        <ul>
          <li>Nature Nanotechnol. 2017</li>
          <li>Chem 2022/2019</li>
          <li>Sci. Adv. 2020×2</li>
          <li>Nature Commun. 2022</li>
          <li>J. Am. Chem. Soc. 2020×3</li>
          <li>Angew. Chem. Int. Ed. 2023/2022/2021×3/2020×3</li>
          <li>Adv. Mater. 2023/2022/2021/2020/2017</li>
          <li>Chem. Rev. 2021/2017；Chem. Soc. Rev. 2017；Acc. Chem. Res. 2018/2015</li>
        </ul>
        <p>总SCI他引≈1.85万次，连续入选全球高被引科学家。</p>
      </div>
    </div>
    ```

    的 Tag 对象 `dcon_tag` 中提取数据。

    Return like:

    ```python
    {
        "教育和工作经历": "2025/04- 复旦大学智能材料与未来能源创新学院 教授/博导\n2020/03-2025/04 复旦大学材料科学系 教授/博导\n2016/03-2020/02 华东师大化学与分子工程学院 教授/博导\n2008/09-2016/02 中科院上海硅酸盐所 研究员/博导\n2002/08-2008/08 同所 博士后→助研→副研\n1997/09-2002/06 南京工业大学 材料学 博士\n1993/09-1997/07 齐鲁工业大学 材料学 学士",
        "研究方向": "材料生物学（无机生物化学与医用功能材料）\n1. 光/电/磁功能材料的合成方法学\n2. 稀土功能材料：光磁学、分子影像、肿瘤诊疗\n3. 功能材料用于脑科学（神经显像与调控）\n常年招收材料、化学、物理、生物、基础医学等背景研究生与博士后。",
        "主讲课程": "《生命、医学与材料》",
        "主要荣誉和奖励": "国家杰青（结题优秀A）\n科技部中青年科技创新领军人才\n上海市自然科学一等奖（2022，第一完成人）\nClarivate全球高被引科学家（2019-2022连续）\n上海市优秀学术带头人等",
        "项目合作单位": "复旦：肿瘤、华山、华东医院\n上海交大新华医院、同济十院\n海军军医大长海/长征医院\nNUS、U Queensland、UTS 等",
        "学术组织兼职": "中国生物材料学会理事、影像材料分会候任主委；BMEMat 副主编；Chem. Soc. Rev./Bioconjugate Chem. 等期刊编委。",
        "近5年代表性论著": "Nature Nanotechnol. 2017\nChem 2022/2019\nSci. Adv. 2020×2\nNature Commun. 2022\nJ. Am. Chem. Soc. 2020×3\nAngew. Chem. Int. Ed. 2023/2022/2021×3/2020×3\nAdv. Mater. 2023/2022/2021/2020/2017\nChem. Rev. 2021/2017；Chem. Soc. Rev. 2017；Acc. Chem. Res. 2018/2015\n总SCI他引≈1.85万次，连续入选全球高被引科学家。"
    }
    ```
    """
    data = {}
    for sub_tag in filter(lambda child: isinstance(child, bs4.Tag), con_tag.children):
        if "person-dcon" in sub_tag.get("class"):
            (heading, contents) = _extract_person_dcon(sub_tag)
            data[heading] = sep.join(contents).replace("\xa0", " ")
        elif "person-con" in sub_tag.get("class"):
            data.update(_extract_person_con(sub_tag))
    return data


def parse_data(text: str) -> Dict[str, str]:
    r"""
    从响应的文本中提取数据。

    Params:

    - text: page() 或 async_page() 返回的结果。

    Return like:

    ```python
    {
        # 必定存在的字段
        "头像": "/_upload/article/images/4c/97/1fea7d1940d58eb0f447863bef41/54ae1324-0c3e-448b-8a8b-8dddd2c91918.png",
        "姓名": "步文博",
        "职称": "教授",

        # 可能存在的字段
        "电话": "021-31243520",
        "邮箱": "wbbu@fudan.edu.cn",
        "办公地点": "复旦大学（江湾校区）化学楼B6075室",
        "课题组主页": "http://faculty.fudan.edu.cn/buwenbo/zh_CN/index.htm",
        "教育和工作经历": "2025/04- 复旦大学智能材料与未来能源创新学院 教授/博导\n2020/03-2025/04 复旦大学材料科学系 教授/博导\n2016/03-2020/02 华东师大化学与分子工程学院 教授/博导\n2008/09-2016/02 中科院上海硅酸盐所 研究员/博导\n2002/08-2008/08 同所 博士后→助研→副研\n1997/09-2002/06 南京工业大学 材料学 博士\n1993/09-1997/07 齐鲁工业大学 材料学 学士",
        "研究方向": "材料生物学（无机生物化学与医用功能材料）\n1. 光/电/磁功能材料的合成方法学\n2. 稀土功能材料：光磁学、分子影像、肿瘤诊疗\n3. 功能材料用于脑科学（神经显像与调控）\n常年招收材料、化学、物理、生物、基础医学等背景研究生与博士后。",
        "主讲课程": "《生命、医学与材料》",
        "主要荣誉和奖励": "国家杰青（结题优秀A）\n科技部中青年科技创新领军人才\n上海市自然科学一等奖（2022，第一完成人）\nClarivate全球高被引科学家（2019-2022连续）\n上海市优秀学术带头人等",
        "项目合作单位": "复旦：肿瘤、华山、华东医院\n上海交大新华医院、同济十院\n海军军医大长海/长征医院\nNUS、U Queensland、UTS 等",
        "学术组织兼职": "中国生物材料学会理事、影像材料分会候任主委；BMEMat 副主编；Chem. Soc. Rev./Bioconjugate Chem. 等期刊编委。",
        "近5年代表性论著": "Nature Nanotechnol. 2017\nChem 2022/2019\nSci. Adv. 2020×2\nNature Commun. 2022\nJ. Am. Chem. Soc. 2020×3\nAngew. Chem. Int. Ed. 2023/2022/2021×3/2020×3\nAdv. Mater. 2023/2022/2021/2020/2017\nChem. Rev. 2021/2017；Chem. Soc. Rev. 2017；Acc. Chem. Res. 2018/2015\n总SCI他引≈1.85万次，连续入选全球高被引科学家。"
    }
    ```
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    soup = BeautifulSoup(text, 'html.parser')

    top_tag = soup.find('div', class_='person-top')
    top_data = _extract_person_top(top_tag)

    con_tag = soup.find('div', class_='person-con')
    con_data = _extract_person_con(con_tag)

    return con_data | top_data
