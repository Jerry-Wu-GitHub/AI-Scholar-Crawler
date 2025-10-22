from __future__ import annotations
from functools import cache
import re
from typing import Any, Dict, Iterable, List, Set

from config.constants import SCHEME



class Document():
    """
    文献对象，可用于储存查询结果。
    """

    def __init__(
        self,
        *,
        creator_cn: Iterable[str] = None,
        creator_en: Iterable[str] = None,
        subject_cn: Iterable[str] = None,
        subject_en: Iterable[str] = None,
        description_cn: str = "",
        description_en: str = "",
        title_cn: str = "",
        title_en: str = "",
        add_title_cn: str = "",
        add_title_en: str = "",
        type: str = "",
        language: str = "",
        general: Iterable[str] = None,
        publisher: str = "",
        issn: str = "",
        doi: str = "",
    ):
        creator_cn = creator_cn or {}
        creator_en = creator_en or {}
        subject_cn = subject_cn or {}
        subject_en = subject_en or {}
        general = general or {}

        self.creator_cn = set(creator_cn)
        self.creator_en = set(creator_en)
        self.creator = self.creator_cn | self.creator_en
        self.subject_cn = set(subject_cn)
        self.subject_en = set(subject_en)
        self.subject = self.subject_cn | self.subject_en
        self.description_cn = description_cn
        self.description_en = description_en
        self.description = self.description_cn + self.description_en
        self.title_cn = title_cn
        self.title_en = title_en
        self.title = self.title_cn + self.title_en
        self.add_title_cn = add_title_cn
        self.add_title_en = add_title_en
        self.add_title = self.add_title_cn + self.add_title_en
        self.type = type
        self.language = language
        self.general = set(general)
        self.publisher = publisher
        self.issn = issn
        self.doi = doi


    def to_json(self) -> Dict[str, str | List[str]]:
        """
        获取对象的可 JSON 化格式。
        """
        return {
            "creator_cn": list(self.creator_cn),
            "creator_en": list(self.creator_en),
            "subject_cn": list(self.subject_cn),
            "subject_en": list(self.subject_en),
            "description_cn": self.description_cn,
            "description_en": self.description_en,
            "title_cn": self.title_cn,
            "title_en": self.title_en,
            "add_title_cn": self.add_title_cn,
            "add_title_en": self.add_title_en,
            "type": self.type,
            "language": self.language,
            "general": list(self.general),
            "publisher": self.publisher,
            "issn": self.issn,
            "doi": self.doi,
        }


    @classmethod
    def from_json(cls, json_data: Dict[str, str | Iterable[str]]) -> Document:
        """
        从对象的 JSON 格式数据转换为对象。
        """
        return Document(**json_data)


    @classmethod
    def from_pnx(cls, pnx: Dict[str, Any]) -> Document:
        """
        从查询结果中的 pnx 字段构造 `Document` 对象。
        """

        #### 提取作者姓名 ####

        # `creator_strings` is like:
        # ["武相军 王春淋 阚海斌", "武相军 王春淋 阚海斌", "武相军 王春淋 阚海斌"]
        creator_strings = sum(
            (
                pnx.get("search", {}).get("creatorcontrib", []),
                pnx.get("search", {}).get("creator", []),
                pnx.get("display", {}).get("creator", []),
                pnx.get("sort", {}).get("author", []),
                pnx.get("addata", {}).get("au", []),
                pnx.get("facets", {}).get("creatorcontrib", []),
            ),
            start = []
        )

        # `creator` is like:
        # {"武相军", "王春淋", "阚海斌"}
        creator_cn: Set[str] = set.union(*(
            set(re.split(r"\s+", creator_string))
            for creator_string in creator_strings
        ), set())

        #### 提取主题 ####

        # `subjects` is like:
        # (
        #     ['分数阶混沌系统', '图像置乱', '密文交错扩散', '彩色图像', '混沌加密'],
        #     ['分数阶混沌系统', '图像置乱', '密文交错扩散', '彩色图像', '混沌加密'],
        #     ['分数阶混沌系统', '图像置乱', '密文交错扩散', '彩色图像', '混沌加密']
        # )
        subjects = (
            pnx.get("search", {}).get("subject", []),
            " ; ".join(pnx.get("display", {}).get("subject", [])).split(" ; "),
            pnx.get("facets", {}).get("topic", []),
        )

        # `subject` is like:
        # {'分数阶混沌系统', '图像置乱', '密文交错扩散', '彩色图像', '混沌加密'}
        subject_cn: Set[str] = set.union(*map(set, subjects))

        #### 提取描述段 ####

        # `description` is like:
        # "为了实现对彩色图像信息的有效保护，提出一种像素置乱及密文交错扩散技术相结合的加密算法。首先对3个分数阶混沌系统产生的混沌序列进行优化改进，得到两组不同的性能优良的混沌密钥序列，并将RGB彩色图像转换为由基色分量组成的灰度图像；然后，利用一组改进的混沌密钥序列对该灰度图像的像素位置进行置乱；最后，利用另一组改进的混沌密钥序列对置乱图像进行2轮基色分量之间的密文交错扩散操作，得到加密图像。仿真实验表明，该算法具有足够大的密钥空间，高度的密钥敏感性，较好的像素分布特性，且在抵抗唯密文攻击、差分攻击、选择明文攻击及统计攻击方面都具有良好的性能，可以广泛地应用于多媒体数据的保密通信中。"
        description_cn: str = "\n".join(
            pnx.get("search", {}).get("description", []) or
            pnx.get("display", {}).get("description", []) or
            pnx.get("addata", {}).get("abstract", [])
        )

        #### 提取标题 ####

        # `title` is like:
        # "基于多分数阶混沌系统的彩色图像加密算法"
        title_cn: str = "\n".join(
            pnx.get("display", {}).get("title", []) or
            pnx.get("sort", {}).get("title", []) or
            pnx.get("addata", {}).get("atitle", [])
        )

        #### 提取附加标题 ####

        # `add_title_cn` is like:
        # "计算机与现代化"
        add_title_cn: str = "\n".join(
            pnx.get("addata", {}).get("jtitle", []) or
            pnx.get("jtitle", [])
        )

        # `add_title_en` is like:
        # "Computer and Modernization"
        add_title_en: str = "\n".join(
            pnx.get("search", {}).get("addtitle", []) or
            pnx.get("addata", {}).get("addtitle", [])
        )

        #### 提取文献类型 ####

        # `type` is like:
        # "article"
        type: str = "\n".join(
            pnx.get("search", {}).get("rsrctype", []) or
            pnx.get("search", {}).get("recordtype", []) or
            pnx.get("display", {}).get("type", []) or
            pnx.get("control", {}).get("recordtype", []) or
            pnx.get("addata", {}).get("genre", [])
        )

        #### 提取文献语言 ####

        # `language` is like:
        # "chi"
        language: str = "\n".join(
            pnx.get("display", {}).get("language", []) or
            pnx.get("facets", {}).get("language", [])
        )

        #### 提取整体的(?)信息 ####

        # `general` is like:
        # {
        #     "河南大学软件学院，河南 开封 475004",
        #     "复旦大学计算机科学技术学院，上海 200433%河南大学计算机与信息工程学院,河南 开封,475004%复旦大学计算机科学技术学院,上海,200433"
        # }
        general: Set[str] = set(pnx.get("search", {}).get("general", []))

        #### 提取发布者 ####

        # `publisher` is like:
        # "河南大学软件学院，河南 开封 475004"
        publisher: str = "\n".join(
            pnx.get("display", {}).get("publisher", []) or
            pnx.get("addata", {}).get("pub", [])
        )

        #### 提取文献的标识符 ####

        # `issn` is like:
        # "1006-2475"
        issn: str = (
            pnx.get("search", {}).get("issn", []) or
            pnx.get("addata", {}).get("issn", []) or
            [""]
        )[0]

        # `doi` is like:
        # "10.3969\/j.issn.1006-2475.2013.11.001"
        doi: str = pnx.get("addata", {}).get("doi", [""])[0]

        #### 整合数据 ####

        return Document(
            creator_cn = creator_cn,
            subject_cn = subject_cn,
            description_cn = description_cn,
            title_cn = title_cn,
            add_title_cn = add_title_cn,
            add_title_en = add_title_en,
            type = type,
            language = language,
            general = general,
            publisher = publisher,
            issn = issn,
            doi = doi,
        )


    def _get_comparable_text(self) -> str:
        subject = "，".join(self.subject_cn)
        texts = (
            text
            for text in map(str.strip, (subject, self.title_cn, self.description_cn))
            if text
        )
        return "。".join(texts)


    def by_teacher_score(self, teacher_info: Dict[str, str]) -> float:
        """
        返回该文献是由这位老师写的得分。

        得分位于 [0, 1] ，值越大，越可能是这位老师写的。
        """
        if teacher_info["name"] not in self.creator:
            return 0
        return SCHEME.text_relevance(teacher_info["subject"], self._get_comparable_text())


    def is_by_teacher(self, teacher_info: Dict[str, str]) -> bool:
        """
        判断这篇文章是否是由这位老师写的。
        """
        return self.by_teacher_score(teacher_info) >= SCHEME.RELEVANCE_THRESHOLD
