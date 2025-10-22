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
        'referer': f'{base_url}/zzjs_39692/list.htm',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'queryObj': 'teacherHome',
    }

    # returnInfos 还能有以下字段：
    # - exField3
    # - exField4
    # - exField5
    # - exFiele7: `""` 、 `"S"` 或 `"K"`。（用途未知）
    # - visitCount: 页面访问次数。
    # - headerPic: 头像图片。
    data = {
        'siteId': site_id,
        # 'pageIndex': '1',
        # 'rows': '999',
        'orders': '[{"field":"firstLetter","type":"asc"}]',
        'returnInfos': '[{"field":"title","name":"title"},{"field":"career","name":"career"},{"field":"firstLetter","name":"firstLetter"},{"field":"exField1","name":"exField1"},{"field":"exField2","name":"exField2"},{"field":"exField6","name":"exField6"},{"field":"cnUrl","name":"cnUrl"}]',
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

    响应返回的数据格式见 data/raw/json/577.json

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

    响应返回的数据格式见 data/raw/json/577.json

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
                'columnId': 37033,
                'siteId': 577,
                'title': '薄格',
                'career': '',
                'exField1': '',
                'exField2': '无',
                'exField6': '无',
                'visitCount': 3466,
                'cnUrl': 'http://cs.fudan.edu.cn/bg/list.htm'
            },
            {
                'columnId': 37039,
                'siteId': 577,
                'title': '曹袖',
                'career': '',
                'exField1': '高级工程师',
                'exField2': '',
                'exField6': '教授级高级工程师',
                'cnUrl': 'http://cs.fudan.edu.cn/cx/list.htm'
            }
        ]

    对各字段的解释：

    - columnId: 该老师（在本学院的？）的唯一编号，处于 [37033, 50429]。
    - siteId: 本学院的编号。
    - title: 老师的姓名。
    - career: 所有老师的都是空字符串。
    - exField1: 可以为以下值及其由 `"、"` 连接而成的字符串，如 `"工程师、专业学位硕导"`。
        - "工程师"
        - "高级工程师"
        - "研究员"
        - "助理研究员"
        - "教授"
        - "副教授"
        - "讲师"
        - "硕导"
        - "专业学位硕导"
        - "博导"
        - "计算机学院学生党总支组织委员"
        - "青年副研究员"
        - "其他中级"
        ...
    - exField2: `""` 、 `"无"` 或 `"兼职教授"`。
    - exField6: 与 exField1 类似，但没有顿号。
    - cnUrl: 在本学院域名下的个人页面链接。
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    try:
        json_data = json.loads(text)
    except json.decoder.JSONDecodeError as error:
        raise DataParseError(f"Invalid JSON format string: {text}") from error

    if "data" not in json_data:
        raise DataParseError(f"Unexcepted JSON format data: {json_data}")

    return json_data["data"]
