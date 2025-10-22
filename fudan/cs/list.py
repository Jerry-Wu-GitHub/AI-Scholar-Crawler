import html
import json
import re
from urllib.parse import urljoin
from typing import Any, Dict, List

import requests
import aiohttp

from errors import DataParseError
from config.constants import COMMON_HEADERS
from .__init__ import domain, base_url, site_id


def _get_arguments(teacher: str) -> Dict[str, str | Dict[str, str]]:
    """
    返回网络请求的必要参数。

    Params:

    - teacher: 老师的姓名的首字母小写，如 `"khb"`。
    """
    headers = COMMON_HEADERS | {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }

    return {
        "url": f'{base_url}/{teacher}/list.htm',
        "headers": headers,
    }


def list_(teacher_or_url: str, **kwargs) -> Dict[str, str]:
    """
    同步请求。

    返回的数据格式见 data/raw/html/cs.khb.html

    Params:

    - teacher_or_url: 老师的姓名的首字母小写，如 `"khb"`，或者是老师在本院的主页 URL，如 `'http://cs.fudan.edu.cn/bg/list.htm'`。
    - kwargs: 传递给 requests.get() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(teacher_or_url)
    if "/" in teacher_or_url:
        # is url
        arguments["url"] = teacher_or_url
    response = requests.get(**arguments)
    response.encoding = response.apparent_encoding
    decoded_html = html.unescape(response.text)
    return parse_data(decoded_html)


async def async_list(teacher_or_url: str, **kwargs) -> Dict[str, str]:
    """
    异步请求。

    返回的数据格式见 data/raw/html/cs.khb.html

    Params:

    - teacher_or_url: 老师的姓名的首字母小写，如 `"khb"`，或者是老师在本院的主页 URL，如 `'http://cs.fudan.edu.cn/bg/list.htm'`。
    - kwargs: 传递给 aiohttp.ClientSession.get() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(teacher_or_url)
    if "/" in teacher_or_url:
        # is url
        arguments["url"] = teacher_or_url
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            text = await response.text()
            decoded_html = html.unescape(text)
            return parse_data(decoded_html)


def _extract_data(class_: str, text: str, string: str) -> str:
    match = re.search(rf'<div class="{class_}">{text}：<span>(.*?)</span></div>', string)
    return match.group(1).strip() if match else ""


def parse_data(text: str) -> Dict[str, str]:
    """
    从响应的文本中提取数据。

    Params:

    - text: list() 或 async_list() 返回的结果。

    Return like:

        {
            'title': '阚海斌',
            'career': '教授、博导',
            'email': 'hbkan@fudan.edu.cn',
            'address': '复旦大学江湾校区二号交叉学科楼 A7021（200438）',
            'degree': '1999，博士学位，复旦大学数学所',
            'research_areas': '编码与信息论，密码学与信息安全，计算复杂性',
            'homepage': 'http://cis.cs.fudan.edu.cn/',
            'image_url': '/_upload/article/images/fa/cf/1542efb94e4f98cdc30545daeb2e/e2fffe0e-d166-43fd-b78b-5b5194e5e60c_s.jpg'
        }

    对各字段的解释：

    - title: 教师姓名。
    - career: 职称。
    - email: 邮箱地址。
    - address: 办公地址。
    - degree: 学位信息。
    - research_areas: 研究领域。
    - homepage: 个人主页链接。
    - image_url: 照片链接。
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    # 提取教师姓名
    title_match = re.search(r'<div class="news_title">(.*?)</div>', text)
    title = title_match.group(1).strip() if title_match else ""

    # 提取职称
    career = _extract_data("news_cara", "职称", text)

    # 提取邮箱
    email = _extract_data("news_email", "邮件", text)

    # 提取地址
    address = _extract_data("news_add", "地址", text)

    # 提取学位
    degree = _extract_data("news_post", "学位", text)

    # 提取研究领域
    research_areas = _extract_data("news_ex", "研究领域", text)

    # 提取个人主页
    homepage_match = re.search(r'<div class="news_gr"><a href="(.*?)">个人主页</a></div>', text)
    homepage = homepage_match.group(1).strip() if homepage_match else ""

    # 提取照片链接
    image_url_match = re.search(r'<div class="news_imgs"><img src="(.*?)"', text)
    image_url = image_url_match.group(1).strip() if image_url_match else ""

    return {
        'title': title,
        'career': career,
        'email': email,
        'address': address,
        'degree': degree,
        'research_areas': research_areas,
        'homepage': homepage,
        'image_url': image_url
    }
