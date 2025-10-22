import json
from typing import Any, Dict, List

import aiohttp
from bs4 import BeautifulSoup
import requests

from errors import DataParseError
from config.constants import COMMON_HEADERS
from ...__init__ import domain, base_url


def _get_arguments() -> Dict[str, str | Dict[str, str]]:
    """
    返回网络请求的必要参数。
    """
    headers = COMMON_HEADERS | {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    return {
        "url": f'{base_url}/Data/List/azc',
        "headers": headers,
        # "verify": False,
    }


def azc(**kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    同步请求。

    响应返回的数据格式见 data/raw/html/未来信息创新学院.html

    Params:

    - kwargs: 传递给 requests.post() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments()
    response = requests.get(**arguments)
    return parse_data(response.text)


async def async_azc(**kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    异步请求。

    响应返回的数据格式见 data/raw/html/未来信息创新学院.html

    Params:

    - kwargs: 传递给 aiohttp.ClientSession.post() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments()
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return parse_data(await response.text())


def parse_data(text: str) -> List[Dict[str, str | int]]:
    """
    从响应的文本中提取数据。

    Params:

    - text: generalQuery() 或 async_generalQuery() 返回的结果。

    Return like:

        [
            {
                "name": "鲍峰",
                "path": "/Data/View/4784",
                "id":   4784,
            },
            {
                "name": "陈涛",
                "path": "/Data/View/2989"
                "id":   2989,
            },
            {
                "name": "陈雄",
                "path": "/Data/View/1170"
                "id":   1170,
            }
        ]

    对各字段的解释：

    - `name`: 教师姓名。
    - `path`: 教师个人页面路径。
    - `id`  : 教师在本学院的唯一编号，处于[953, 4899]。
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    soup = BeautifulSoup(text, 'html.parser')
    teachers = []

    for a_tag in soup.find_all('a', class_ = "people", attrs = {'href': True}):
        name = a_tag.get_text(strip = True)
        path = a_tag.get('href')
        id_  = int(path.split("/")[-1])
        if name and path:
            teachers.append({
                'name': name,
                'path': path,
                'id'  : id_ ,
            })
    return teachers
