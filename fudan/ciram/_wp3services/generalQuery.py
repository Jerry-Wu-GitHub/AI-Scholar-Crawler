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
        'referer': f'{base_url}/cslm/list.htm',
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
        'columnId': '50802',
        # 'pageIndex': '1',
        # 'rows': '999',
        'orders': '[{"field":"letter","type":"asc"}]',
        'returnInfos': '[{"field":"title","name":"title"},{"field":"f9","name":"f9"},{"field":"f1","name":"f1"},{"field":"f2","name":"f2"},{"field":"f4","name":"f4"},{"field":"shortTitle","name":"shortTitle"},{"field":"subTitle","name":"subTitle"},{"field":"imgPath","name":"imgPath"},{"field":"letter","name":"letter"},{"field":"url","name":"url"},]',
        # 'conditions': '[{"field":"scope","value":0,"judge":"="}]',
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

    响应返回的数据格式见 data/raw/json/1083.json

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

    响应返回的数据格式见 data/raw/json/1083.json

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
                "title": "艾剑良",
                "f9": "正高级",
                "f1": "教授",
                "f2": "智能飞行控制与复杂异构无人系统",
                "f4": "航空航天系",
                "shortTitle": "教学科研",
                "subTitle": "",
                "imgPath": "/_upload/article/images/5b/4a/545e489b4b4da371227ab6ad399b/b4013ef9-70fa-4256-83a2-e049da3bef46.jpg",
                "url": "https://aero-mech.fudan.edu.cn/9e/10/c25828a171536/page.htm",
                "id": 737027,
                "wapUrl": "https://aero-mech.fudan.edu.cn/9e/10/c25828a171536/page.htm",
                "trueWapUrl": "",
                "publishTime": "2025-05-21 16:14:49.0",
                "publisher": "柴宏宇",
                "publisherId": 19366,
                "visitCount": 22,
                "mircImgPath": "/_upload/article/images/5b/4a/545e489b4b4da371227ab6ad399b/b4013ef9-70fa-4256-83a2-e049da3bef46_s.jpg",
                "siteArtId": 3815881
            }
        ]

    对各字段的解释：

    - title: 教师姓名。
    - f9: 职级，如 "正高级"、"副高级"、"中级" 等。
    - f1: 职称，如 "教授"、"青年副研究员" 等。
    - f2: 研究方向。
    - f4: 所属系所。
    - shortTitle: 短标题。
    - subTitle: 子标题。
    - imgPath: 照片图片路径。
    - url: 教师个人页面链接。
    - id: 教师在学校的唯一编号，处于 [736936, 748907]。
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
