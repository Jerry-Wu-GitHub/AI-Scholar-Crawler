import aiohttp
import requests
import urllib.parse
from typing import Any, Dict, List

from ......__init__ import domain, base_url
from config.constants import COMMON_HEADERS


def _get_arguments(institution: str) -> Dict[str, str]:
    """
    获取必要的请求参数。

    Params:

    - `institution`: 发起请求者的身份，如 `"FDU"` 。
    """
    referer = urllib.parse.urljoin(base_url, "/primo-explore/search") + f"?vid={institution.lower()}"

    headers = COMMON_HEADERS | {
        'Accept': 'application/json, text/plain, */*',
        'Connection': 'keep-alive',
        'Referer': referer,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    params = {
        'isGuest': 'true',
        'lang': 'zh_CN',
        'targetUrl': urllib.parse.quote(referer, safe = ''),
        'viewId': 'UnknownView',
    }

    return {
        "url": urllib.parse.urljoin(base_url, f'/primo_library/libweb/webservices/rest/v1/guestJwt/{institution.upper()}'),
        "params": params,
        "headers": headers,
    }


def guestJwt(institution: str, **kwargs: Dict[str, Any]):
    """
    获取 jwtToken 。

    同步函数。

    Params:

    - `institution`: 发起查询请求者的身份，如 `"FDU"` 。
    - `kwargs`: 其他传递给 `requests.get()` 的参数，可以设置 timeout、 proxies 等。

    Return like:

    ```python
    "eyJraWQiOiJwcmltb0V4cGxvcmVQcml2YXRlS2V5LUZEVSIsImFsZyI6IkVTMjU2In0.eyJpc3MiOiJQcmltbyIsImp0aSI6IiIsImNtanRpIjpudWxsLCJleHAiOjE3NjA2MDQzNDUsImlhdCI6MTc2MDUxNzk0NSwidXNlciI6ImFub255bW91cy0xMDE1XzA4NDU0NSIsInVzZXJOYW1lIjpudWxsLCJ1c2VyR3JvdXAiOiJHVUVTVCIsImJvckdyb3VwSWQiOm51bGwsInViaWQiOm51bGwsImluc3RpdHV0aW9uIjoiRkRVIiwidmlld0luc3RpdHV0aW9uQ29kZSI6IkZEVSIsImlwIjoiMjAyLjEyMC4yMzUuMjEzIiwicGRzUmVtb3RlSW5zdCI6bnVsbCwib25DYW1wdXMiOiJ0cnVlIiwibGFuZ3VhZ2UiOiJ6aF9DTiIsImF1dGhlbnRpY2F0aW9uUHJvZmlsZSI6IiIsInZpZXdJZCI6ImZkdSIsImlsc0FwaUlkIjpudWxsLCJzYW1sU2Vzc2lvbkluZGV4IjoiIiwiand0QWx0ZXJuYXRpdmVCZWFjb25JbnN0aXR1dGlvbkNvZGUiOiJGRFUifQ.apI1i7fVTnoW13i0FvPMtEL8vT_7q3rHjwhn5CpLlV4DP1vj1h4aITrGNWffw9EIauqowk3F99RX9j765Wl2WQ"
    ```
    """
    arguments = kwargs | _get_arguments(institution)
    response = requests.get(**arguments)
    return response.text


async def async_guestJwt(institution: str, **kwargs: Dict[str, Any]):
    """
    获取 jwtToken 。

    同步函数。

    Params:

    - `institution`: 发起查询请求者的身份，如 `"FDU"` 。
    - `kwargs`: 其他传递给 `requests.get()` 的参数，可以设置 timeout、 proxies 等。

    Return like:

    ```python
    "eyJraWQiOiJwcmltb0V4cGxvcmVQcml2YXRlS2V5LUZEVSIsImFsZyI6IkVTMjU2In0.eyJpc3MiOiJQcmltbyIsImp0aSI6IiIsImNtanRpIjpudWxsLCJleHAiOjE3NjA2MDQzNDUsImlhdCI6MTc2MDUxNzk0NSwidXNlciI6ImFub255bW91cy0xMDE1XzA4NDU0NSIsInVzZXJOYW1lIjpudWxsLCJ1c2VyR3JvdXAiOiJHVUVTVCIsImJvckdyb3VwSWQiOm51bGwsInViaWQiOm51bGwsImluc3RpdHV0aW9uIjoiRkRVIiwidmlld0luc3RpdHV0aW9uQ29kZSI6IkZEVSIsImlwIjoiMjAyLjEyMC4yMzUuMjEzIiwicGRzUmVtb3RlSW5zdCI6bnVsbCwib25DYW1wdXMiOiJ0cnVlIiwibGFuZ3VhZ2UiOiJ6aF9DTiIsImF1dGhlbnRpY2F0aW9uUHJvZmlsZSI6IiIsInZpZXdJZCI6ImZkdSIsImlsc0FwaUlkIjpudWxsLCJzYW1sU2Vzc2lvbkluZGV4IjoiIiwiand0QWx0ZXJuYXRpdmVCZWFjb25JbnN0aXR1dGlvbkNvZGUiOiJGRFUifQ.apI1i7fVTnoW13i0FvPMtEL8vT_7q3rHjwhn5CpLlV4DP1vj1h4aITrGNWffw9EIauqowk3F99RX9j765Wl2WQ"
    ```
    """
    arguments = kwargs | _get_arguments(institution)
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return await response.text()
