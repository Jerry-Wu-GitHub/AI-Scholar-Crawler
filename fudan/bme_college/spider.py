"""
获取老师的数据。
"""

import asyncio
from typing import Any, Dict, List

from .main import (
    main,
    async_main,
)
from ._wp3services import (
    generalQuery,
    async_generalQuery,
)
from config.constants import CONCURRENCY_NUMBER
from .__init__ import college_name


def _assembly_data(general_info: Dict[str, Any], basic_info: Dict[str, str]) -> Dict[str, str]:
    academic_title = basic_info.get("职称", "") or general_info["exField7"]
    homepage = basic_info.get("课题组主页", "") or general_info["cnUrl"]
    subject = basic_info.get("主要研究方向", "") or basic_info.get("研究领域", "")
    
    return {
        "person_id"       : str(general_info["columnId"])     ,
        "name"            : general_info["title"]             ,
        "college"         : college_name                      ,
        "academic_title"  : academic_title                    ,
        "profile"         : basic_info.get("学习/工作经历", ""),
        "personal_website": homepage                          ,
        "subject"         : subject                           ,
        "email"           : general_info["email"]             ,
        "phone"           : general_info["phone"]             ,
    }


def general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    同步函数。

    获取生物医学工程与技术创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    for general_info in general_infos:
        basic_info = main(general_info["cnUrl"])
        result.append(_assembly_data(general_info, basic_info))
    return result


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    异步并发加速。

    获取生物医学工程与技术创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = await async_generalQuery(**kwargs)
    result: List[Dict[str, str]] = []
    semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)
    async def fetch_info(general_info: Dict[str, Any]) -> Dict[str, str]:
        async with semaphore:
            basic_info = await async_main(general_info["cnUrl"])
            return _assembly_data(general_info, basic_info)

    tasks = [fetch_info(general_info) for general_info in general_infos]
    result = await asyncio.gather(*tasks)
    return result
