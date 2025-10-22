import asyncio
from typing import Any, Dict, List

from .list import (
    list_,
    async_list,
)
from .page import (
    page,
    async_page,
)
from config.constants import CONCURRENCY_NUMBER
from .__init__ import college_name


def _assembly_data(general_info: Dict[str, Any], basic_info: Dict[str, str]) -> Dict[str, str]:
    return {
        "person_id"       : general_info["id"]  ,
        "name"            : general_info["name"],
        "college"         : college_name        ,
        "academic_title"  : basic_info.get("职称", "")         ,
        "profile"         : basic_info.get("教育和工作经历", ""),
        "personal_website": basic_info.get("课题组主页", "")   ,
        "subject"         : basic_info.get("研究方向", "")     ,
        "email"           : basic_info.get("邮箱", "") or basic_info.get("Email", ""),
        "phone"           : basic_info.get("电话", "")         ,
    }


def general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    同步函数。

    获取智能材料与未来能源创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = list_(**kwargs)
    result: List[Dict[str, str]] = []
    for general_info in general_infos:
        basic_info = page(general_info["path"])
        result.append(_assembly_data(general_info, basic_info))
    return result


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    异步并发加速。

    获取智能材料与未来能源创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = await async_list(**kwargs)
    result: List[Dict[str, str]] = []
    semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)
    async def fetch_info(general_info: Dict[str, Any]) -> Dict[str, str]:
        async with semaphore:
            basic_info = await async_page(general_info["path"])
            return _assembly_data(general_info, basic_info)

    tasks = [fetch_info(general_info) for general_info in general_infos]
    result = await asyncio.gather(*tasks)
    return result
