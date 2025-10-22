"""
获取老师的数据。
"""

import asyncio
from typing import Any, Dict, List

from ._wp3services import (
    generalQuery,
    async_generalQuery,
)
from config.constants import CONCURRENCY_NUMBER
from .__init__ import college_name


def _assembly_data(general_info: Dict[str, Any]) -> Dict[str, str]:
    return {
        "person_id"       : str(general_info["id"]),
        "name"            : general_info["title"]  ,
        "college"         : college_name           ,
        "academic_title"  : general_info['f1']     ,
        "profile"         : ""                     ,
        "personal_website": general_info["url"] if (general_info["url"] != "#") else "",
        "subject"         : general_info["f2"]     ,
        "email"           : ""                     ,
        "phone"           : ""                     ,
    }


def general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    同步函数。

    获取智能机器人与先进制造创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    for general_info in general_infos:
        result.append(_assembly_data(general_info))
    return result


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    异步并发加速。

    获取智能机器人与先进制造创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = await async_generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)
    async def fetch_info(general_info: Dict[str, Any]) -> Dict[str, str]:
        async with semaphore:
            return _assembly_data(general_info)

    tasks = [fetch_info(general_info) for general_info in general_infos]
    result = await asyncio.gather(*tasks)
    return result
