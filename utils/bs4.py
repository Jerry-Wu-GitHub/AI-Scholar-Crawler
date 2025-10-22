from typing import List

import bs4


def extract_strings(tag: bs4.Tag) -> List[str]:
    """
    按顺序提取出标签 `tag` 及其所有子标签的 `string` 属性。
    """
    result = []
    for child in tag.children:
        if isinstance(child, bs4.Tag):
            result.extend(extract_strings(child))
        elif child.string:
            result.append(child.string)
    return result
