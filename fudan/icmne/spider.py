"""
获取老师的数据。
"""

import asyncio
from typing import Any, Dict, List

from .page import (
    page,
    async_page,
    parse_data,
)
from ._wp3services import (
    generalQuery,
    async_generalQuery,
)
from config.constants import CONCURRENCY_NUMBER
from .__init__ import college_name


def _assembly_data(general_info: Dict[str, Any], basic_info: Dict[str, str]) -> Dict[str, str]:
    return {
        "person_id"       : str(general_info["id"])             ,
        "name"            : general_info["title"]               ,
        "college"         : college_name                        ,
        "academic_title"  : f"{general_info['f8']}、{general_info['f2']}".strip("、"),
        "profile"         : basic_info["educational_background"],
        "personal_website": basic_info["homepage"] if basic_info["homepage"] else general_info["url"],
        "subject"         : basic_info["research_areas"]        ,
        "email"           : basic_info["email"]                 ,
        "phone"           : basic_info["phone"]                 ,
    }


def general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    同步函数。

    获取集成电路与微纳电子创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    for general_info in general_infos:
        basic_info = page(general_info["url"])
        result.append(_assembly_data(general_info, basic_info))
    return result


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    异步并发加速。

    获取集成电路与微纳电子创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = await async_generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)
    async def fetch_info(general_info: Dict[str, Any]) -> Dict[str, str]:
        async with semaphore:
            basic_info = await async_page(general_info["url"])
            return _assembly_data(general_info, basic_info)

    tasks = [fetch_info(general_info) for general_info in general_infos]
    result = await asyncio.gather(*tasks)
    return result
