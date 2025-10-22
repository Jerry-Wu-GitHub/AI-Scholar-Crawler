import asyncio
from importlib import import_module
from itertools import chain
from typing import Any, Dict, List

from config.constants import COLLEGES
from src.deduplicate import is_same_person, merge_info


spiders = {
    college: import_module(f"fudan.{college}.spider")
    for college in COLLEGES
}


async def async_general_information(**kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
    name_mapping: Dict[str, List[Dict[str, str]]] = {}

    async def fetch_info(college: str, **kwargs: Dict[str, Any]) -> None:
        """
        结果会存储到 name_mapping 中。
        """
        if not college in spiders:
            raise KeyError(f"未知的学院代号 {college}")

        infos = await spiders[college].async_general_information(**kwargs)

        for info in infos:
            name = info["name"]
            if name in name_mapping:
                for (idx, other) in enumerate(name_mapping[name], start = 0):
                    if is_same_person(info, other):
                        name_mapping[name][idx] = merge_info(info, other)
                        break
                else:
                    # 未发现重复的人
                    name_mapping[name].append(info)
            else:
                name_mapping[name] = [info]

        print(f"college `{college}` finished!")

    await asyncio.gather(
        *(fetch_info(college) for college in COLLEGES),
        return_exceptions = True
    )

    infos = list(chain.from_iterable(name_mapping.values()))
    return infos
