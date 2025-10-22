"""
获取老师的数据。
"""

import asyncio
from typing import Any, Dict, List

from fudan.cs.list import (
    list_,
    async_list,
)
from ._wp3services import (
    generalQuery,
    async_generalQuery,
)
from config.constants import CONCURRENCY_NUMBER
from .__init__ import college_name


def _assembly_data(general_info: Dict[str, Any], basic_info: Dict[str, str]) -> Dict[str, str]:
    return {
        "person_id"       : str(general_info["columnId"]),
        "name"            : general_info["title"]        ,
        "college"         : college_name                 ,
        "academic_title"  : general_info["exField1"]     ,
        "profile"         : basic_info["degree"]         ,
        "personal_website": basic_info["homepage"]       ,
        "subject"         : basic_info["research_areas"] ,
        "email"           : basic_info["email"]          ,
        "phone"           : ""                           ,
    }


def general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    同步函数。

    获取计算与智能创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    for general_info in general_infos:
        basic_info = list_(general_info["cnUrl"])
        result.append(_assembly_data(general_info, basic_info))
    return result


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    异步并发加速。

    获取计算与智能创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = await async_generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)
    async def fetch_info(general_info: Dict[str, Any]) -> Dict[str, str]:
        async with semaphore:
            basic_info = await async_list(general_info["cnUrl"])
            return _assembly_data(general_info, basic_info)

    tasks = [fetch_info(general_info) for general_info in general_infos]
    result = await asyncio.gather(*tasks)
    return result
