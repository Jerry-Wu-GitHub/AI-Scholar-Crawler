from typing import Dict

from config.constants import COLLEGES

def _existing_fields_number(info: Dict[str, str]) -> int:
    """
    返回信息 `info` 的非空字段数。
    """
    return sum(map(bool, info.values()))


def _info_length(info: Dict[str, str]) -> int:
    """
    返回有效信息的长度。
    """
    length = 0
    for field in ("academic_title", "profile", "subject"):
        length += len(info[field])
    return length


def _less_info(info1: Dict[str, str], info2: Dict[str, str]) -> bool:
    """
    Return: info1.信息量 < info2.信息量
    """
    existing_fields_number1 = _existing_fields_number(info1)
    existing_fields_number2 = _existing_fields_number(info2)
    if existing_fields_number1 != existing_fields_number2:
        return existing_fields_number1 < existing_fields_number2
    return _info_length(info1) < _info_length(info2)


def _is_college_homepage(url: str) -> bool:
    """
    判断 `url` 是否是老师在学院官网的个人页面。
    """
    for college in COLLEGES:
        if url.find(f"{college}.fudan.") != -1:
            return True
    return False


def _score_homepage(url: str) -> bool:
    """
    为 `url` “评分”。
    """
    if not url:
        return 0
    if _is_college_homepage(url):
        return 1
    return len(url) + 1


def merge_info(info1: Dict[str, str], info2: Dict[str, str]) -> Dict[str, str]:
    """
    判断两条 `name` 相同的信息是否属于同一个老师。

    Params:

    - `info1`、`info2`: fudan.*.spider.general_information() 或 fudan.*.spider.async_general_information() 返回的列表中的元素。
    """
    person_id = max(info1["person_id"], info2["person_id"], key = int)
    name = max(info1["name"], info2["name"])

    if   "兼聘" in info1["academic_title"]:
        more_info = info2
    elif "兼聘" in info2["academic_title"]:
        more_info = info1
    else:
        more_info = info2 if _less_info(info1, info2) else info1
    college = more_info["college"]
    academic_title = more_info["academic_title"]

    personal_website = max(info1["personal_website"], info2["personal_website"], key = _score_homepage)

    subject = max(info1["subject"], info2["subject"], key = len)
    profile = max(info1["profile"], info2["profile"], key = len)
    email   = max(info1["email"],   info2["email"],   key = len)
    phone   = max(info1["phone"],   info2["phone"],   key = len)

    return {
        "person_id":        person_id       ,
        "name":             name            ,
        "college":          college         ,
        "academic_title":   academic_title  ,
        "personal_website": personal_website,
        "subject":          subject         ,
        "profile":          profile         ,
        "email":            email           ,
        "phone":            phone           ,
    }
