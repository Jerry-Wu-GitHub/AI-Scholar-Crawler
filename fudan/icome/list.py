import json
import re
from typing import Any, Dict, List

import aiohttp
from bs4 import BeautifulSoup
import requests

from errors import DataParseError
from config.constants import COMMON_HEADERS
from .__init__ import domain, base_url, site_id


def _get_arguments() -> Dict[str, str]:
    headers = COMMON_HEADERS | {
        'authority': domain,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
    }

    return {
        "url": f"{base_url}/49292/list.htm",
        "headers": headers,
    }


def list_(**kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    同步请求。

    响应返回的数据格式见 data/raw/html/智能材料与未来能源创新学院.html

    Params:

    - kwargs: 传递给 requests.post() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments()
    response = requests.post(**arguments)
    return parse_data(response.text)


async def async_list(**kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    异步请求。

    响应返回的数据格式见 data/raw/html/智能材料与未来能源创新学院.html

    Params:

    - kwargs: 传递给 aiohttp.ClientSession.post() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments()
    async with aiohttp.ClientSession() as session:
        async with session.post(**arguments) as response:
            return parse_data(await response.text())


def parse_data(text: str) -> List[Dict[str, str | int]]:
    """
    从响应的文本中提取数据。

    Params:

    - text: list() 或 async_list() 返回的结果。

    Return like:

        [
            {
                "name": "傅正文",
                "path": "/21/ac/c49294a729516/page.htm",
                "id": 729516
            },
            {
                "name": "卢红斌",
                "path": "/21/a9/c49294a729513/page.htm"
                "id": 729513
            },
            {
                "name": "沈伟",
                "path": "/21/a6/c49294a729510/page.htm"
                "id": 729510
            }
        ]

    对各字段的解释：

    - `name`: 教师姓名。
    - `path`: 教师个人页面链接。
    - `id`: 教师在学校的的唯一编号，处于 [729217, 731172]。
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    soup = BeautifulSoup(text, 'html.parser')
    teachers = []

    for li in soup.find_all('li', attrs={'name': True}):
        a_tag = li.find('a')
        if a_tag:
            name = a_tag.get_text(strip=True)
            path = a_tag.get('href')
            id_match = re.search(pattern = r"\/c\d{5}a(\d{6})\/page\.htm", string = path)
            if name and path and id_match:
                teachers.append({
                    'name': name,
                    'path': path,
                    'id': id_match.group(1),
                })
    return teachers
