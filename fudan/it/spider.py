"""
注意，这个网站有反爬机制，同一个 ip 不能在短时间内发出太多请求。

之后可以搞 IP 池，预计可以减少一分钟的运行时间。
"""

import asyncio
import random
from typing import Any, Dict, List

from .Data import (
    azc as query,
    async_azc as async_query,
    view,
    async_view,
)
from config.constants import CONCURRENCY_NUMBER, RETRANSMISSION
from .__init__ import college_name

# 3并发，耗时 135 秒，4 次错误，0/143 个失败。
# 4并发，耗时 104 秒，1 次错误，0/143 个失败。
# 5并发，耗时 144 秒，12 次错误，0/143 个失败。
# 6并发，耗时 137 秒，21 次错误，0/143 个失败。
# 7并发，耗时 165 秒，29 次错误，0/143 个失败。
# 8并发，耗时 173 秒，30 次错误，0/143 个失败。
# 10并发，耗时 178 秒，63 次错误，0/143 个失败
CONCURRENCY_NUMBER = 6


def _assembly_data(general_info: Dict[str, Any], basic_info: Dict[str, str]) -> Dict[str, str]:
    return {
        "person_id"       : str(general_info["id"])           ,
        "name"            : general_info["name"]              ,
        "college"         : college_name                      ,
        "academic_title"  : basic_info.get("职称", "")        ,
        "profile"         : basic_info.get("学习工作经历", ""),
        "personal_website": basic_info.get("课题组主页", "")  ,
        "subject"         : basic_info.get("研究兴趣", "")    ,
        "email"           : basic_info.get("电子邮箱", "")    ,
        "phone"           : basic_info.get("电话", "")        ,
    }


def general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    同步函数。

    获取未来信息创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = query(**kwargs)
    result: List[Dict[str, str]] = []
    for general_info in general_infos:
        basic_info = view(general_info["path"])
        result.append(_assembly_data(general_info, basic_info))
    return result


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    异步并发加速。

    获取未来信息创新学院的老师的基本信息。
    """
    general_infos: List[Dict[str, Any]] = await async_query(**kwargs)
    result: List[Dict[str, str]] = []
    semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)
    async def fetch_info(general_info: Dict[str, Any]) -> Dict[str, str]:
        async with semaphore:
            transmissions = 1
            parsing_successful = False
            basic_info = {}
            while (not parsing_successful) and (transmissions <= RETRANSMISSION):
                await asyncio.sleep(random.random())
                try:
                    basic_info = await async_view(general_info["path"])
                    parsing_successful = True
                except AttributeError as error:
                    print(f"解析 {general_info['name']} 老师的基本数据时发生 {transmissions} 次错误: {str(error)[:100]}")
                    await asyncio.sleep(1)
                transmissions += 1
            return _assembly_data(general_info, basic_info)
    tasks = [fetch_info(general_info) for general_info in general_infos]
    result = await asyncio.gather(*tasks)
    return result
