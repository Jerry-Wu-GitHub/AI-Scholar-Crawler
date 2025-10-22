"""
爬取图书馆的论文数据。

Usage:

1. 普通用法：

    ```python
    session = Session()
    paper_infos: List[Document] = asyncio.run(session.async_paper_informations(teacher_infos)) # teacher_infos: List[Dict[str, str]]
    ```

2. 指定每个老师查询的论文的最大数量：

    ```python
    session = Session(limit = 100)
    ...same as the code above
    ```

3. 筛选论文数据时，应用多线程并发加速：

    ```python
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers = 4) as executor:
        session = Session(executor = executor)
        ...same as the code above
    ```

本模块的耗时操作在于 Session._filter_articles() ，而非网络请求。
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
from typing import Any, Dict, Iterable, List, Tuple
from types import NoneType
import warnings

from config.constants import CONCURRENCY_NUMBER, RETRANSMISSION, MAX_WORKERS
from .hosted.fudan_primo.primo_library.libweb.webservices import (
    guestJwt,
    async_guestJwt,
    pnxs,
    async_pnxs,
)
from .document import Document
from .__init__ import VALID_INSTITUTIONS


CONCURRENCY_NUMBER = max(MAX_WORKERS, 20)


class Session():
    """
    复用同一个 jwtToken ，减少重复获取 jwtToken 的开销。
    """

    def __init__(
        self,
        *,
        jwt_token   : str = None,
        limit       : int = 10,
        institution : str = "fdu",
        executor    : ThreadPoolExecutor = None,
        **kwargs    : Dict[str, Any]
    ):
        """
        初始化一个 `Session` 对象。

        Params:

        - `jwt_token`: 可选的初始 jwtToken。
        - `limit`    : 默认的最大查询结果条目数。
        - `institution`: 默认的
        """
        if not isinstance(jwt_token, (str, NoneType)):
            raise TypeError(f"`jwt_token` is expected to be `str` object, but got `{jwt_token!r}`")

        if not isinstance(limit, int):
            raise TypeError(f"`limit` is expected to be `int` object, but got `{limit!r}`")
        if limit < 0:
            raise ValueError(f"`limit` is expected to be a positive integer, but got {limit!r}")
        if limit == 0:
            warnings.warn(f"`limit` is expected to be a positive integer, but got {limit!r}", UserWarning)

        if not isinstance(institution, str):
            raise TypeError(f"`institution` is expected to be `str` object, but got `{institution!r}`")
        if institution.lower() not in VALID_INSTITUTIONS:
            raise ValueError(f"`institution` is expected to be in {VALID_INSTITUTIONS}, but got {institution!r}")

        if not isinstance(executor, (ThreadPoolExecutor, NoneType)):
            raise TypeError(f"`executor` is expected to be `ThreadPoolExecutor` object, but got `{executor!r}`")

        self.limit = limit
        self.institution = institution

        self.default_kwargs = kwargs

        self.jwt_token = jwt_token or ""
        if not self.jwt_token:
            self.update_token(**kwargs)

        self.executor = executor


    def update_token(self, **kwargs: Dict[str, Any]) -> None:
        """
        获取一个新的 jwtToken。

        Params:

        - `kwargs`: 传递给 guestJwt() 的参数。
        """
        arguments = {"institution": self.institution} | self.default_kwargs | kwargs
        self.jwt_token = guestJwt(**arguments)


    async def async_update_token(self, **kwargs: Dict[str, Any]) -> None:
        """
        获取一个新的 jwtToken。

        Params:

        - `kwargs`: 传递给 guestJwt() 的参数。
        """
        arguments = {"institution": self.institution} | self.default_kwargs | kwargs
        self.jwt_token = await async_guestJwt(**arguments)


    def _filter_articles(self, teacher_info: Dict[str, str], pnxs: Iterable[Dict[str, Any]]) -> List[Document]:
        """
        筛选出可能是该老师写的论文。
        """
        # 筛选出类型为“article”（文章）的文献
        all_articles: List[Document] = [
            document
            for document in map(Document.from_pnx, pnxs)
            if document.type == "article"
        ]

        # 多线程加速判断
        if self.executor:
            is_by_teacher: Tuple[bool] = tuple(self.executor.map(Document.is_by_teacher, all_articles, [teacher_info] * len(all_articles)))
        else:
            print(False)
            is_by_teacher: Tuple[bool] = tuple(article.is_by_teacher(teacher_info) for article in all_articles)

        return [article for (idx, article) in enumerate(all_articles, start = 0) if is_by_teacher[idx]]


    def search_articles(self, teacher_info: Dict[str, str], **kwargs: Dict[str, Any]) -> List[Document]:
        """
        查询该老师的论文数据。

        同步方法。
        """
        arguments = {
            "jwt_token": self.jwt_token,
            "search_text": teacher_info["name"],
            "limit": self.limit,
            "institution": self.institution,
        } | self.default_kwargs | kwargs
        return self._filter_articles(teacher_info, pnxs(**arguments))


    async def async_search_articles(self, teacher_info: Dict[str, str], **kwargs: Dict[str, Any]) -> List[Document]:
        """
        查询该老师的论文数据。

        异步方法。
        """
        arguments = {
            "jwt_token": self.jwt_token,
            "search_text": teacher_info["name"],
            "limit": self.limit,
            "institution": self.institution,
        } | self.default_kwargs | kwargs
        transmissions = 1
        pnx_infos = []
        parsing_successful = False
        while (not parsing_successful) and (transmissions <= RETRANSMISSION):
            await asyncio.sleep(random.random())
            try:
                pnx_infos = await async_pnxs(**arguments)
                parsing_successful = True
            except (Exception, ConnectionResetError) as error:
                print(f"解析 {teacher_info['person_id']},{teacher_info['name']} 老师的论文数据时发生 {transmissions} 次错误: {str(error)[:50]}")
                await asyncio.sleep(1)
            transmissions += 1
        return self._filter_articles(teacher_info, pnx_infos)


    def paper_information(self, teacher_info: Dict[str, str], **kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        同步函数。

        获取指定老师的论文信息。
        """
        return [
            _assembly_data(teacher_info, article)
            for article in self.search_articles(teacher_info, **kwargs)
        ]


    async def async_paper_information(self, teacher_info: Dict[str, str], **kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        同步函数。

        获取指定老师的论文信息。
        """
        return [
            _assembly_data(teacher_info, article)
            for article in await self.async_search_articles(teacher_info, **kwargs)
        ]


    def paper_informations(self, teacher_infos: Iterable[Dict[str, str]], **kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        同步函数。

        获取所有老师的论文信息。
        """
        paper_infos: List[Dict[str, str]] = []
        for teacher_info in teacher_infos:
            paper_infos.extend(self.paper_information(teacher_info, **kwargs))
        return paper_infos


    async def async_paper_informations(self, teacher_infos: Iterable[Dict[str, str]], **kwargs: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        异步函数，异步并发加速。

        获取所有老师的论文信息。
        """
        paper_infos: List[Dict[str, str]] = []
        semaphore = asyncio.Semaphore(CONCURRENCY_NUMBER)

        async def fetch_info(teacher_info: Dict[str, str], **kwargs: Dict[str, Any]) -> None:
            async with semaphore:
                print(f"开始爬取 {teacher_info["name"]} 老师的论文数据。")
                paper_infos.extend(await self.async_paper_information(teacher_info, **kwargs))

        tasks = [fetch_info(teacher_info, **kwargs) for teacher_info in teacher_infos]
        await asyncio.gather(*tasks)
        return paper_infos



def _assembly_data(teacher_info: Dict[str, str], article: Document) -> Dict[str, str]:
    return {
        "person_id": teacher_info["person_id"],
        "author_cn": teacher_info["name"],
        "author_en": "",
        "author_email": teacher_info["email"],
        "title_cn": article.title_cn,
        "title_en": article.title_en,
        "keyword_cn": "；".join(article.subject_cn),
        "keyword_en": "；".join(article.subject_en),
        "article_info": f"{article.title_cn} {article.title_en} {article.description_cn} {article.description_en}",
    }
