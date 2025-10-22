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
        'referer': f'{base_url}/szdw/list.htm',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'queryObj': 'teacherHome',
    }

    data = {
        'siteId': site_id,
        'level': '1',
        'articleType': '1',
        # 'pageIndex': '1',
        # 'rows': '999',
        'orders': '[{"field":"letter","type":"asc"}]',
        'returnInfos': '[{"field":"title","name":"title"},{"field":"exField1","name":"exField1"},{"field":"exField7","name":"exField7"},{"field":"exField3","name":"exField3"},{"field":"exField10","name":"exField10"},{"field":"phone","name":"phone"},{"field":"firstLetter","name":"firstLetter"},{"field":"email","name":"email"},{"field":"cnUrl","name":"cnUrl"},{"field":"headerPic","name":"headerPic"}]',
        'conditions': '[{"field":"scope","value":0,"judge":"="}]',
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

    响应返回的数据格式见 data/raw/json/1082.json

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

    响应返回的数据格式见 data/raw/json/1082.json

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
                "columnId": 49599,
                "siteId": 1082,
                "title": "陈国平",
                "exField1": "副高级",
                "exField7": "副研究员",
                "exField3": "微纳系统中心",
                "exField10": "",
                "phone": "",
                "email": "gpchenapple@fudan.edu.cn",
                "cnUrl": "http://bme-college.fudan.edu.cn/cgp/main.htm",
                "headerPic": "/_upload/article/images/34/5c/1072ad0a485d95250ee1b1263efd/95465c11-eb5f-4a7d-a6cb-6e1737ea4c6a.png"
            },
            {
                "columnId": 49605,
                "siteId": 1082,
                "title": "陈欣荣",
                "exField1": "正高级",
                "exField7": "青年研究员",
                "exField3": "生物医学工程技术研究所",
                "exField10": "",
                "phone": "021-54237181",
                "email": "chenxinrong@fudan.edu.cn",
                "cnUrl": "http://bme-college.fudan.edu.cn/cxr/main.htm",
                "headerPic": "/_upload/article/images/83/60/41e292d7424581be2ab16a0f9f9c/8a114b76-e938-445f-b283-f5948ce6b585.png"
            }
        ]

    对各字段的解释：

    - columnId: 该老师（在本学院的？）的唯一编号，处于 [49590, 51723]。
    - siteId: 本学院的编号。
    - title: 老师的姓名。
    - exField1: 职称级别，如 "正高级"、"副高级"、"初中级" 等。
    - exField7: 具体的职称，如 "教授"、"青年研究员" 等。
    - exField3: 所属部门或研究所。
    - exField10: 可能包含一些额外信息，如人才计划等。
    - phone: 联系电话。
    - email: 电子邮箱地址。
    - cnUrl: 在本学院域名下的个人页面链接。
    - headerPic: 头像图片的 URL 。
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
