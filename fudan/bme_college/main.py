"""
此 main 非彼 main 。

解析在本学院域名下的个人页面。
"""

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


def _get_arguments(url: str) -> Dict[str, str]:
    """
    返回网络请求的必要参数。

    Params:

    - url: 老师的个人页面的链接，如 `"http://bme-college.fudan.edu.cn/cxr/main.htm"`。
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
        "url": url,
        "headers": headers,
    }


def main(url: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - url: 老师的个人页面的链接，如 `"http://bme-college.fudan.edu.cn/cxr/main.htm"`。
    - kwargs: 传递给 requests.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/陈国平.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(url)
    response = requests.get(**arguments)
    return parse_data(response.text)


async def async_main(url: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - url: 老师的个人页面的链接，如 `"http://bme-college.fudan.edu.cn/cxr/main.htm"`。
    - kwargs: 传递给 aiohttp.ClientSession.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/陈国平.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return parse_data(await response.text())


def _extract_art_info(art_info_tag: bs4.Tag | None) -> str:
    """
    从结构为

    ```html
    <div class="art_info">
        <img src="/_upload/article/images/34/5c/1072ad0a485d95250ee1b1263efd/95465c11-eb5f-4a7d-a6cb-6e1737ea4c6a.png" alt="">
    </div>
    ```

    的 Tag 对象 `art_info_tag` 中提取数据。

    Return like:

    ```python
    "/_upload/article/images/34/5c/1072ad0a485d95250ee1b1263efd/95465c11-eb5f-4a7d-a6cb-6e1737ea4c6a.png"
    ```
    """
    if not art_info_tag:
        return ""

    img_tag = art_info_tag.find("img", attrs = {"src": True})
    img_url = img_tag.get("src", default = "")

    return img_url


def _extract_title(title_tag: bs4.Tag | None) -> str:
    """
    从结构为

    ```html
    <div class="title">
        陈国平
        <span>（）</span>
    </div>
    ```

    的 Tag 对象 `title_tag` 中提取数据。

    Return like:

    ```python
    "陈国平"
    ```
    """
    if not title_tag:
        return ""

    # 只取直接子节点中的字符串部分
    texts = (
        child.string.strip()
        for child in title_tag.children
        if isinstance(child, bs4.NavigableString)
    )
    return "".join(texts)


def _extract_post(post_tag: bs4.Tag | None) -> str:
    """
    从结构为

    ```html
    <div class="post" id="title-field">
        副研究员
        <span class="co">、</span>
    </div>
    ```

    的 Tag 对象 `post_tag` 中提取数据。

    Return like:

    ```python
    "副研究员"
    ```
    """
    if not post_tag:
        return ""
    return "".join(map(str.strip, extract_strings(post_tag))).strip("、无")


def _extract_l_or_r(tag: bs4.Tag | None) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="l">
        <p>
            <span>系所中心：</span>
            <span class="co">微纳系统中心</span>
        <p>
            <span>职称：</span>
            <span class="co" id="post-field">副研究员</span>
        </p>
        <p>
            <span>职务：</span>
            <span class="co"></span>
        </p>
        <p>
            <span>研究领域：</span>
            <span class="co"></span>
        </p>
        <!--<p><span>学术任职：</span><span class="co"></span>
    </p>-->
        <p>
            <span>个人简介：</span>
            <span class="co"></span>
        </p>
    </div>
    ```

    或

    ```html
    <div class="r">
        <p>
            <span>联系电话：</span>
            <span class="co"></span>
        </p>
        <p>
            <span>电子邮箱：</span>
            <span class="co">gpchenapple@fudan.edu.cn</span>
        </p>
        <p>
            <span>办公地点：</span>
            <span class="co">江湾交叉二号楼A7005室</span>
        </p>
        <!--<p><span>主要研究方向：</span><span class="co">生物医学传感器</span></p>-->
    </div>
    ```

    的 Tag 对象 `tag` 中提取数据。

    Return like:

    ```python
    {
        # 可能有的字段
        "系所中心": "微纳系统中心"             ,
        "职称"    : "副研究员"                ,
        "职务"    : ""                        ,
        "研究领域": ""                        ,
        "个人简介": ""                        ,
        "联系电话": ""                        ,
        "电子邮箱": "gpchenapple@fudan.edu.cn",
        "办公地点": "江湾交叉二号楼A7005室"    ,
    }
    ```
    """
    result = {}
    if not tag:
        return result
    for p in tag.find_all("p"):
        text = "".join("".join(extract_strings(span)).strip() for span in p.children if span.name == "span")
        if "：" in text:
            (key, value) = text.split("：", 1)
            result[key] = value
    return result


def _extract_flex_row(flex_row_tag: bs4.Tag | None) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="flex-row">
        <div class="l">
            <p><span>系所中心：</span><span class="co">微纳系统中心</span>
            <p><span>职称：</span><span class="co" id="post-field">副研究员</span></p>
            <p><span>职务：</span><span class="co"></span></p>
            <p><span>研究领域：</span><span class="co"></span></p>
            <!--<p><span>学术任职：</span><span class="co"></span></p>-->
            <p><span>个人简介：</span><span class="co"></span></p>
        </div>
        <div class="r">
            <p><span>联系电话：</span><span class="co"></span></p>
            <p><span>电子邮箱：</span><span class="co">gpchenapple@fudan.edu.cn</span></p>
            <p><span>办公地点：</span><span class="co">江湾交叉二号楼A7005室</span></p>
            <!--<p><span>主要研究方向：</span><span class="co">生物医学传感器</span></p>-->
        </div>
    </div>
    ```

    的 Tag 对象 `flex_row_tag` 中提取数据。

    Return like: 见 _extract_l_or_r()
    """
    if not flex_row_tag:
        return {}
    l_tag = flex_row_tag.find("div", class_ = "l")
    r_tag = flex_row_tag.find("div", class_ = "r")
    return _extract_l_or_r(l_tag) | _extract_l_or_r(r_tag)


def _extract_news_info(news_info_tag: bs4.Tag | None) -> Dict[str, str]:
    """
    就是在 <div class="flex-row"></div> 外面套了个 <div class="flex-row"></div>。

    见 _extract_flex_row()
    """
    if not news_info_tag:
        return {}
    flex_row_tag = news_info_tag.find("div", class_ = "flex-row")
    return _extract_flex_row(flex_row_tag)


def _extract_art_wz(art_wz_tag: bs4.Tag) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="art_wz">
        <div class="title">...</div>
        <div class="post" id="title-field">...</div>
        <div class="news_info">...</div>
    </div>
    ```

    的 Tag 对象 `art_wz_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        "姓名"    : "陈国平"                  ,
        "职称"    : "副研究员"                ,
        
        # 可能有的字段
        "系所中心": "微纳系统中心"             ,
        "职务"    : ""                        ,
        "研究领域": ""                        ,
        "个人简介": ""                        ,
        "联系电话": ""                        ,
        "电子邮箱": "gpchenapple@fudan.edu.cn",
        "办公地点": "江湾交叉二号楼A7005室"    ,
    }
    ```
    """
    title_tag = art_wz_tag.find("div", class_ = "title")
    title = _extract_title(title_tag)

    post_tag = art_wz_tag.find("div", class_ = "post", id = "title-field")
    academic_title = _extract_post(post_tag)

    news_info_tag = art_wz_tag.find("div", class_ = "news_info")
    info = _extract_news_info(news_info_tag)

    info["姓名"] = title
    info["职称"] = academic_title

    return info


def _extract_mtop(mtop_tag: bs4.Tag) -> Dict[str, str]:
    """
    从结构为

    ```html
    <div class="mtop">
        <div class="art_info">...</div>
        <div class="art_wz">...</div>
    </div>
    ```

    的 Tag 对象 `mtop_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        "头像"    : "/_upload/article/images/34/5c/1072ad0a485d95250ee1b1263efd/95465c11-eb5f-4a7d-a6cb-6e1737ea4c6a.png",
        "姓名"    : "陈国平"                  ,
        "职称"    : "副研究员"                ,
        
        # 可能有的字段
        "系所中心": "微纳系统中心"             ,
        "职务"    : ""                        ,
        "研究领域": ""                        ,
        "个人简介": ""                        ,
        "联系电话": ""                        ,
        "电子邮箱": "gpchenapple@fudan.edu.cn",
        "办公地点": "江湾交叉二号楼A7005室"    ,
    }
    ```
    """
    art_info_tag = mtop_tag.find("div", class_ = "art_info")
    img_url = _extract_art_info(art_info_tag)

    art_wz_tag = mtop_tag.find("div", class_ = "art_wz")
    info = _extract_art_wz(art_wz_tag)

    info["头像"] = img_url

    return info


def _extract_tt(tt_tag: bs4.Tag) -> str:
    """
    从结构为

    ```html
    <div class="tt">
        学习/工作经历
    </div>
    ```

    的 Tag 对象 `tt_tag` 中提取数据。

    Return like:

    ```python
    "学习/工作经历"
    ```
    """
    if not tt_tag:
        return ""
    return tt_tag.get_text().strip()


def _extract_con2(con2_tag: bs4.Tag | None) -> str:
    r"""
    从结构为

    ```html
    <div class="con con2">
        <p>1989年9月-1993年6月，安徽农业大学，林学，农学学士</p>
        <p>1996年9月-1999年6月，中科院上海应用物理研究所（原子核研究所），粒子物理与原子核物理，理学硕士</p>
        <p>1999年9月-2003年12月，上海交通大学，生物医学工程，工学博士</p>
        <p>2003年12月-至今，复旦大学，副研究员</p>
    </div>
    ```

    的 Tag 对象 `tt_tag` 中提取数据。

    Return like:

    ```python
    "1989年9月-1993年6月，安徽农业大学，林学，农学学士\n1996年9月-1999年6月，中科院上海应用物理研究所（原子核研究所），粒子物理与原子核物理，理学硕士\n1999年9月-2003年12月，上海交通大学，生物医学工程，工学博士\n2003年12月-至今，复旦大学，副研究员"
    ```
    """
    if not con2_tag:
        return ""
    return "\n".join(
        "".join(extract_strings(p))
        for p in con2_tag.find_all("p")
    )


def _extract_art_con(art_con_tag: bs4.Tag) -> Tuple[str, str]:
    r"""
    从结构为

    ```html
    <div class="art_con">
        <div class="tt">学习/工作经历</div>
        <div class="con con2">...</div>
    </div>
    ```

    的 Tag 对象 `art_con_tag` 中提取数据。

    Return like:

    ```python
    ("学习/工作经历", "1989年9月-1993年6月，安徽农业大学，林学，农学学士\n1996年9月-1999年6月，中科院上海应用物理研究所（原子核研究所），粒子物理与原子核物理，理学硕士\n1999年9月-2003年12月，上海交通大学，生物医学工程，工学博士\n2003年12月-至今，复旦大学，副研究员")
    ```
    """
    tt_tag = art_con_tag.find("div", class_ = "tt")
    field = _extract_tt(tt_tag)

    con2_tag = art_con_tag.find("div", class_ = "con2")
    value = _extract_con2(con2_tag)

    return (field, value)


def _extract_mbottom(mbottom_tag: bs4.Tag | None) -> Dict[str, str]:
    r"""
    从结构为

    ```html
    <div class="mbottom">
        <div class="art_con">...</div>
        <div class="art_con">...</div>
        <div class="art_con">...</div>
        <div class="art_con">...</div>
        <div class="art_con">...</div>
        <div class="art_con">...</div>
        <div class="art_con" style="display: none;">...</div>
        <!--<div class="art_con">...</div>-->
    </div>
    ```

    的 Tag 对象 `mbottom_tag` 中提取数据。

    Return like:

    ```python
    {
        "个人简介": "",
        "主要研究方向": "生物医学传感器",
        "学术任职": "",
        "学习/工作经历": "1989年9月-1993年6月，安徽农业大学，林学，农学学士\n1996年9月-1999年6月，中科院上海应用物理研究所（原子核研究所），粒子物理与原子核物理，理学硕士\n1999年9月-2003年12月，上海交通大学，生物医学工程，工学博士\n2003年12月-至今，复旦大学，副研究员",
    }
    ```
    """
    if not mbottom_tag:
        return {}
    return dict(
        _extract_art_con(art_con_tag)
        for art_con_tag in mbottom_tag.find_all("div", class_ = "art_con")
    )


def _extract_teach_info(teach_info_tag: bs4.Tag) -> Dict[str, str]:
    r"""
    从结构为

    ```html
    <div class="teach_info" frag="窗7" portletmode="simpleList">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" class="wp_article_list_table">
            <tbody>
                <tr>
                    <td>
                        <div class="mtop">...</div>
                        <div class="mbottom">...</div>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    ```

    的 Tag 对象 `teach_info_tag` 中提取数据。

    Return like:

    ```python
    {
        # 一定有的字段
        "头像"    : "/_upload/article/images/34/5c/1072ad0a485d95250ee1b1263efd/95465c11-eb5f-4a7d-a6cb-6e1737ea4c6a.png",
        "姓名"    : "陈国平"                  ,
        "职称"    : "副研究员"                ,
        
        # 可能有的字段
        "系所中心": "微纳系统中心"             ,
        "职务"    : ""                        ,
        "研究领域": ""                        ,
        "联系电话": ""                        ,
        "电子邮箱": "gpchenapple@fudan.edu.cn",
        "办公地点": "江湾交叉二号楼A7005室"    ,
        "个人简介": "",
        "主要研究方向": "生物医学传感器",
        "学术任职": "",
        "学习/工作经历": "1989年9月-1993年6月，安徽农业大学，林学，农学学士\n1996年9月-1999年6月，中科院上海应用物理研究所（原子核研究所），粒子物理与原子核物理，理学硕士\n1999年9月-2003年12月，上海交通大学，生物医学工程，工学博士\n2003年12月-至今，复旦大学，副研究员",
    }
    ```
    """
    mtop_tag = teach_info_tag.find("div", class_ = "mtop")
    mtop_info = _extract_mtop(mtop_tag)

    mbottom_tag = teach_info_tag.find("div", class_ = "mbottom")
    mbottom_info = _extract_mbottom(mbottom_tag)

    return mtop_info | mbottom_info


def parse_data(text: str) -> Dict[str, str]:
    """
    从响应的文本中提取数据。

    Params:

    - text: main() 或 async_main() 返回的结果。

    Return like: 见 _extract_teach_info()
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    soup = BeautifulSoup(text, 'html.parser')

    teach_info_tag = soup.find("div", class_ = "teach_info")

    return _extract_teach_info(teach_info_tag)
