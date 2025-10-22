import aiohttp
import json
import requests
import urllib.parse
from typing import Any, Dict, List

from .......__init__ import domain, base_url
from config.constants import COMMON_HEADERS
from errors import DataParseError


def _get_referer_query_str(search_text: str, bulk_size: int, institution: str) -> str:
    return urllib.parse.urlencode({
        "institution"   : institution.upper(),
        "vid"           : institution.lower(),
        "tab"           : "default_tab",
        "search_scope"  : "default_scope",
        "mode"          : "basic",
        "displayMode"   : "full",
        "bulkSize"      : str(bulk_size),
        "highlight"     : "true",
        "dum"           : "true",
        "query"         : f"any,contains,{search_text}",
    })


def _get_query_str(search_text: str, limit: int, institution: str) -> str:
    return urllib.parse.urlencode({
        "acTriggered"                       : "false",
        "blendFacetsSeparately"             : "true",
        "citationTrailFilterByAvailability" : "true",
        "getMore"                           : "0",
        "inst"                              : institution.upper(),
        "isCDSearch"                        : "false",
        "lang"                              : "zh_CN",
        "limit"                             : str(limit),
        "mode"                              : "basic",
        "newspapersActive"                  : "false",
        "newspapersSearch"                  : "false",
        "offset"                            : "0",
        "otbRanking"                        : "false",
        "pcAvailability"                    : "true",
        "q"                                 : f"any,contains,{search_text}",
        "qExclude"                          : "",
        "qInclude"                          : "",
        "refEntryActive"                    : "false",
        "rtaLinks"                          : "true",
        "scope"                             : "default_scope",
        "searchInFulltextUserSelection"     : "false",
        "skipDelivery"                      : "Y",
        "sort"                              : "rank",
        "tab"                               : "default_tab",
        "vid"                               : institution.lower(),
    })


def _get_arguments(jwt_token: str, search_text: str, limit: int, institution: str) -> Dict[str, str]:
    """
    获取必要的请求参数。

    Params:

    - `jwt_token`  : guestJwt() 返回的令牌。
    - `search_text`: 搜索框内的文本，如 `"阚海斌"` 。
    - `limit`      : 单次返回的搜索结果数，如 `10` 。
    - `institution`: 发起请求者的身份，如 `"FDU"` 。
    """
    referer = urllib.parse.urljoin(base_url, "/primo-explore/search") + "?" + _get_referer_query_str(search_text, limit, institution)

    url = urllib.parse.urljoin(base_url, "/primo_library/libweb/webservices/rest/primo-explore/v1/pnxs") + "?" + _get_query_str(search_text, limit, institution)

    headers = COMMON_HEADERS | {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {jwt_token}',
        'Connection': 'keep-alive',
        'Referer': referer,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    return {
        "url": url,
        "headers": headers,
    }


def pnxs(jwt_token: str, search_text: str, limit: int, institution: str, **kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    发送查询请求。

    同步函数。

    Params:

    - `jwt_token`  : guestJwt() 返回的令牌。
    - `search_text`: 搜索框内的文本，如 `"阚海斌"` 。
    - `limit`      : 单次返回的搜索结果数，如 `10` 。
    - `institution`: 发起请求者的身份，如 `"FDU"` 。
    - `kwargs`     : 其他传递给 requests.get() 的参数，可以设置 timeout、 proxies 等。

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(jwt_token, search_text, limit, institution)
    response = requests.get(**arguments)
    return parse_data(response.text)


async def async_pnxs(jwt_token: str, search_text: str, limit: int, institution: str, **kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    发送查询请求。

    异步函数。

    Params:

    - `jwt_token`  : guestJwt() 返回的令牌。
    - `search_text`: 搜索框内的文本，如 `"阚海斌"` 。
    - `limit`      : 单次返回的搜索结果数，如 `10` 。
    - `institution`: 发起请求者的身份，如 `"FDU"` 。
    - `kwargs`     : 其他传递给 requests.get() 的参数，可以设置 timeout、 proxies 等。

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(jwt_token, search_text, limit, institution)
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return parse_data(await response.text())


def parse_data(text: str) -> List[Dict[str, Any]]:
    """
    解析响应的返回内容。

    Params:

    - `text`: pnxs() 或 async_pnxs() 的响应内容。

    Return like:

    ```python
    [
        {
            /* 3.1 delivery：全文获取指示 */
            "delivery": {
                "fulltext": ["fulltext"],               // 有全文
                "delcategory": ["Remote Search Resource"] // 全文在远程库
            },

            /* 3.2 search：检索与分面字段 */
            "search": {
                "sourceid": ["2RA"],                    // 数据源代码：万方
                "creatorcontrib": ["武相军 王春淋 阚海斌"],
                "creator": ["武相军 王春淋 阚海斌"],
                "creationdate": ["2013"],
                "subject": [
                    "分数阶混沌系统",
                    "图像置乱",
                    "密文交错扩散",
                    "彩色图像",
                    "混沌加密"
                ],
                "rsrctype": ["article"],
                "description": [
                    "为了实现对彩色图像信息的有效保护，提出一种像素置乱及密文交错扩散技术相结合的加密算法。首先对3个分数阶混沌系统产生的混沌序列进行优化改进，得到两组不同的性能优良的混沌密钥序列，并将RGB彩色图像转换为由基色分量组成的灰度图像；然后，利用一组改进的混沌密钥序列对该灰度图像的像素位置进行置乱；最后，利用另一组改进的混沌密钥序列对置乱图像进行2轮基色分量之间的密文交错扩散操作，得到加密图像。仿真实验表明，该算法具有足够大的密钥空间，高度的密钥敏感性，较好的像素分布特性，且在抵抗唯密文攻击、差分攻击、选择明文攻击及统计攻击方面都具有良好的性能，可以广泛地应用于多媒体数据的保密通信中。"
                ],
                "title": ["基于多分数阶混沌系统的彩色图像加密算法"],
                "startdate": ["2013"],
                "addtitle": ["Computer and Modernization"],
                "recordid": ["eNo9jz1Lw0Acxm9QsNR-CMHBJfF_d7m73CjFNyi4dA-XtzZBU20Q7awUlaJTUepQBxcXlRYstOin8RL9FkYqTg88_HgefgitYjCp5HI9NqM0TUwMwA1iCWYSwNTE2ATAC6j03y-hSppGLgAhnDLJSkjq4fRzeq0fB_qim_Vfv-_esskkG_Xy8SyfDfPBuX5_-roc6fsPfXajrx70Szd_vs3G_WW0GKr9NKj8ZRnVtzbr1R2jtre9W92oGR6T2LAC1xYAUipXYd8Wli0YcO4z8DihXBCiwlAoapOQC6kCLkMQLhNMUhJY1KVltDafPVFJqJKGE7eO20lx6MRp3Dn1m7-quDDEBboyR71mK2kcRQV82I4OVLvjWEJg2-Kc_gBR1Gph"],
                "general": [
                    "河南大学软件学院，河南 开封 475004",
                    "复旦大学计算机科学技术学院，上海 200433%河南大学计算机与信息工程学院,河南 开封,475004%复旦大学计算机科学技术学院,上海,200433"
                ],
                "enddate": ["2013"],
                "issn": ["1006-2475"],
                "scope": ["2RA", "92L", "CQIGP", "W92", "~WA", "2B.", "4A8", "92I", "93N", "PSX", "TCJ"],
                "recordtype": ["article"],
                "fulltext": ["true"]
            },

            /* 3.3 display：前端展示字段 */
            "display": {
                "identifier": [
                    "ISSN: 1006-2475",
                    "DOI: 10.3969/j.issn.1006-2475.2013.11.001"
                ],
                "creator": ["武相军 王春淋 阚海斌"],
                "subject": ["分数阶混沌系统 ; 图像置乱 ; 密文交错扩散 ; 彩色图像 ; 混沌加密"],
                "rights": ["Copyright © Wanfang Data Co. Ltd. All Rights Reserved."],
                "ispartof": ["计算机与现代化, 2013 (11), p.1-7"],
                "publisher": ["河南大学软件学院，河南 开封 475004"],
                "description": ["为了实现对彩色图像信息的有效保护，提出一种像素置乱及密文交错扩散技术相结合的加密算法……"],
                "language": ["chi"],
                "source": [
                    "维普期刊资源整合服务平台",
                    "Alma/SFX Local Collection",
                    "万方数据库"
                ],
                "type": ["article"],
                "title": ["基于多分数阶混沌系统的彩色图像加密算法"]
            },

            /* 3.4 control：系统内部控制 */
            "control": {
                "recordid": ["TN_cdi_wanfang_journals_jsjyxdh201311001"],
                "sourceid": ["wanfang_jour_chong"],
                "iscdi": ["true"],
                "cqvipid": ["47718466"],
                "recordtype": ["article"],
                "originalsourceid": ["FETCH-LOGICAL-c591-4eb870099aba1d874875066d50c6236722aff7a382f679ae69f07b575932e43b3"],
                "sourceformat": ["XML"],
                "wanfjid": ["jsjyxdh201311001"],
                "sourcetype": ["Aggregation Database"],
                "sourcerecordid": ["jsjyxdh201311001"],
                "sourcesystem": ["PC"],
                "addsrcrecordid": ["eNo9jz1Lw0Acxm9QsNR-CMHBJfF_d7m73CjFNyi4dA-XtzZBU20Q7awUlaJTUepQBxcXlRYstOin8RL9FkYqTg88_HgefgitYjCp5HI9NqM0TUwMwA1iCWYSwNTE2ATAC6j03y-hSppGLgAhnDLJSkjq4fRzeq0fB_qim_Vfv-_esskkG_Xy8SyfDfPBuX5_-roc6fsPfXajrx70Szd_vs3G_WW0GKr9NKj8ZRnVtzbr1R2jtre9W92oGR6T2LAC1xYAUipXYd8Wli0YcO4z8DihXBCiwlAoapOQC6kCLkMQLhNMUhJY1KVltDafPVFJqJKGE7eO20lx6MRp3Dn1m7-quDDEBboyR71mK2kcRQV82I4OVLvjWEJg2-Kc_gBR1Gph"]
            },

            /* 3.5 links：外部可访问链接 */
            "links": {
                "openurl": ["$$Topenurl_article"],
                "thumbnail": ["$$Uhttp://image.cqvip.com/vip1000/qk/97264X/97264X.jpg"],
                "openurlfulltext": ["$$Topenurlfull_article"]
            },

            /* 3.6 sort：排序键 */
            "sort": {
                "creationdate": ["2013"],
                "author": ["武相军 王春淋 阚海斌"],
                "title": ["基于多分数阶混沌系统的彩色图像加密算法"]
            },

            /* 3.7 addata：引文/导出标准化字段 */
            "addata": {
                "date": ["2013"],
                "issue": ["11"],
                "ristype": ["JOUR"],
                "format": ["journal"],
                "spage": ["1"],
                "abstract": ["为了实现对彩色图像信息的有效保护……"],
                "atitle": ["基于多分数阶混沌系统的彩色图像加密算法"],
                "addtitle": ["Computer and Modernization"],
                "pages": ["1-7"],
                "au": ["武相军 王春淋 阚海斌"],
                "issn": ["1006-2475"],
                "epage": ["7"],
                "genre": ["article"],
                "tpages": ["7"],
                "jtitle": ["计算机与现代化"],
                "risdate": ["2013"],
                "pub": ["河南大学软件学院，河南 开封 475004"],
                "doi": ["10.3969/j.issn.1006-2475.2013.11.001"]
            },

            /* 3.8 facets：分面导航值 */
            "facets": {
                "frbrtype": ["5"],
                "creatorcontrib": ["武相军 王春淋 阚海斌"],
                "creationdate": ["2013"],
                "toplevel": ["online_resources"],
                "frbrgroupid": ["cdi_FETCH-LOGICAL-c591-4eb870099aba1d874875066d50c6236722aff7a382f679ae69f07b575932e43b3"],
                "rsrctype": ["articles"],
                "topic": ["分数阶混沌系统", "图像置乱", "密文交错扩散", "彩色图像", "混沌加密"],
                "language": ["chi"],
                "jtitle": ["计算机与现代化"],
                "collection": [
                    "维普期刊资源整合服务平台",
                    "中文科技期刊数据库-CALIS站点",
                    "中文科技期刊数据库-7.0平台",
                    "中文科技期刊数据库-工程技术",
                    "中文科技期刊数据库-镜像站点",
                    "Wanfang Data Journals - Hong Kong",
                    "WANFANG Data Centre",
                    "Wanfang Data Journals",
                    "万方数据期刊 - 香港版",
                    "China Online Journals (COJ)",
                    "China Online Journals (COJ)"
                ],
                "prefilter": ["articles"]
            }
        },
        ...
    ]
    ```
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    try:
        json_data = json.loads(text)
    except json.decoder.JSONDecodeError as error:
        raise DataParseError(f"Invalid JSON format string: {text}") from error

    if "docs" not in json_data:
        raise DataParseError(f"Unexcepted JSON format data: {json_data}")

    return [doc.get("pnx", {}) for doc in json_data["docs"]]
