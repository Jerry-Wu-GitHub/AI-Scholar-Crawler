import json
from typing import Any, Dict, List

import aiohttp
import requests

from errors import DataParseError
from config.constants import COMMON_HEADERS
from ..__init__ import domain, base_url, site_id


def _get_arguments() -> Dict[str, str | Dict[str, str]]:
    """
    返回网络请求的必要参数。
    """
    headers = COMMON_HEADERS | {
        'authority': domain,
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': base_url,
        'referer': f'{base_url}/apy/list.htm',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'queryObj': 'articles',
    }

    data = {
        'siteId': site_id,
        # 'pageIndex': '1',
        # 'rows': '999',
        'columnId': '48925',
        'orders': '[{"field":"letter","type":"asc"}]',
        'returnInfos': '[{"field":"letter","name":"letter"},{"field":"title","name":"title"},{"field":"url","name":"url"},{"field":"f8","name":"f8"},{"field":"f2","name":"f2"},{"field":"f1","name":"f1"},{"field":"imgPath","name":"imgPath"}]',
        # 'conditions': '[{"conditions":[{"field":"scope","value":1,"judge":"="},{"field":"f1","value":"%%","judge":"like"},{"field":"letter","value":"%%","judge":"like"}]}]',
        'articleType': '1',
        'level': '1',
    }

    return {
        "url": f'{base_url}/_wp3services/generalQuery',
        "headers": headers,
        "params": params,
        "data": data,
    }


def generalQuery(**kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    同步请求。

    响应返回的数据格式见 data/raw/json/1074.json

    Params:

    - kwargs: 传递给 requests.post() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments()
    response = requests.post(**arguments)
    return parse_data(response.text)


async def async_generalQuery(**kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    异步请求。

    响应返回的数据格式见 data/raw/json/1074.json

    Params:

    - kwargs: 传递给 aiohttp.ClientSession.post() 的额外参数，可以设置 timeout、 proxies 等。

    Return: 见 parse_data()
    """
    arguments = kwargs | _get_arguments()
    async with aiohttp.ClientSession() as session:
        async with session.post(**arguments) as response:
            return parse_data(await response.text())


def parse_data(text: str) -> List[Dict[str, Any]]:
    """
    从响应的文本中提取数据。

    Params:

    - text: generalQuery() 或 async_generalQuery() 返回的结果。

    Return like:

        [
            {
                "title": "边历峰",
                "url": "http://icmne.fudan.edu.cn/17/4b/c48925a726859/page.htm",
                "f8": "研究员",
                "f2": "博士生导师",
                "f1": "正高级",
                "imgPath": "/_upload/article/images/b6/0f/4f5f84a54f92aeefe24a570d34e1/3f40a809-2219-4ac3-a6a1-972548c8b1c7.jpg",
                "id": 726859,
                "wapUrl": "http://icmne.fudan.edu.cn/17/4b/c48925a726859/page.htm",
                "trueWapUrl": "",
                "publishTime": "2025-04-27 20:01:36.0",
                "publisher": "刘莎",
                "publisherId": 19169,
                "visitCount": 2130,
                "mircImgPath": "/_upload/article/images/b6/0f/4f5f84a54f92aeefe24a570d34e1/3f40a809-2219-4ac3-a6a1-972548c8b1c7_s.jpg",
                "siteArtId": 3773667
            }
        ]

    对各字段的解释：

    - title: 教师姓名。
    - url: 教师个人页面链接。
    - f8: 职称，如 "教授"、"研究员" 等。
    - f2: 导师类型，如 "博士生导师"、"硕士生导师" 等。
    - f1: 职级，如 "正高级"、"副高级"、"中级" 等。
    - imgPath: 照片图片路径。
    - id: 教师在学校的唯一编号，处于 [726856, 740488]。
    - wapUrl: 手机端页面链接。
    - trueWapUrl: 真实手机端页面链接。
    - publishTime: 发布时间。
    - publisher: 发布者。
    - publisherId: 发布者编号。
    - visitCount: 页面访问次数。
    - mircImgPath: 缩略图路径。
    - siteArtId: 站点文章编号。
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    try:
        json_data = json.loads(text)
    except json.decoder.JSONDecodeError as error:
        raise DataParseError(f"Invalid JSON format string: {text}") from error

    if "data" not in json_data:
        raise DataParseError(f"Unexpected JSON format data: {json_data}")

    return json_data["data"]
