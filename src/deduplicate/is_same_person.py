import re
from typing import Dict, Set


def _is_fdu_id(id_: str, /) -> bool:
    """
    判断一个 id 是否是老师在整个学校的唯一编号。
    """
    return id_.startswith("7") and (len(id_) == 6)


def _is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\d{8,11}", phone))


def _split_phone(phone_str: str) -> Set[str]:
    return set(filter(_is_valid_phone, map(str.strip, re.split("[-,]", phone_str))))


def is_same_person(info1: Dict[str, str], info2: Dict[str, str]) -> bool:
    """
    判断两条 `name` 相同的信息是否属于同一个老师。

    Params:

    - `info1`、`info2`: fudan.*.spider.general_information() 或 fudan.*.spider.async_general_information() 返回的列表中的元素。

    Return:

    - `True` if these two pieces of information belong to the same teacher, else `False`.
    """
    # 若两条信息的 `person_id` 字段都是老师在整个学校的唯一编号
    if _is_fdu_id(info1["person_id"]) and _is_fdu_id(info2["person_id"]):
        return info1["person_id"] == info2["person_id"]

    # 若姓名不同，则不是同一个人
    if info1["name"] != info2["name"]:
        return False

    # 判断 email 是否相同
    if info1["email"] and info2["email"]:
        return info1["email"] == info2["email"]

    # 判断 phone 是否有交集
    if _split_phone(info1["phone"]) & _split_phone(info2["phone"]):
        return True

    # 判断其中一方的 email 和 phone 是否都为空
    if not ((info1["email"] or info1["phone"]) and (info2["email"] or info2["phone"])):
        return True

    return False
