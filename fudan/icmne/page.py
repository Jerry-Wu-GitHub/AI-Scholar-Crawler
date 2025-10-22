import re
from typing import Any, Dict, List

import aiohttp
import bs4
from bs4 import BeautifulSoup
import requests

from utils.bs4 import extract_strings
from errors import DataParseError
from config.constants import COMMON_HEADERS
from .__init__ import domain, base_url, site_id


def _get_arguments(url: str) -> Dict[str, str | Dict[str, str]]:
    """
    返回网络请求的必要参数。

    Params:

    - url: 老师的个人页面的 URL 。
    """
    headers = COMMON_HEADERS | {
        'authority': domain,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'cache-control': 'max-age=0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
    }

    return {
        "url": url,
        "headers": headers,
    }


def page(url: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - url: 老师的个人页面的 URL，如 https://icmne.fudan.edu.cn/2d/59/c48925a732505/page.htm 。
    - kwargs: 传递给 requests.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/曾璇.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(url)
    response = requests.get(**arguments)
    return parse_data(response.text)


async def async_page(url: str, **kwargs: Dict[str, Any]) -> Dict[str, str]:
    """
    Params:

    - url: 老师的个人页面的 URL，如 https://icmne.fudan.edu.cn/2d/59/c48925a732505/page.htm 。
    - kwargs: 传递给 aiohttp.ClientSession.get() 的额外参数，可以设置 timeout、 proxies 等。

    响应的文本见 data/raw/html/曾璇.html

    Return like: 见 parse_data()
    """
    arguments = kwargs | _get_arguments(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(**arguments) as response:
            return parse_data(await response.text())


def _extract_window11(soup: BeautifulSoup, sep: str = '\n') -> Dict[str, str]:
    r"""
    主要是提取研究方向和教育背景。
    如果在该老师的页面上找不到研究方向或教育背景，则在返回的字典中不会出现该键。

    Return like:

    {
        '研究方向': '集成电路设计自动化\n模拟电路设计自动化：包括电路模拟，模拟电路的行为级建模及模拟，模拟电路版图设计自动化\n高速互连电路分析和综合，包括互连线参数提取、互连线模型降阶、高速时钟设计\n可制造性设计研究，包括工艺偏差下的电路模拟、统计静态时序分析、带参数模型降阶算法；光刻仿真、铜互连工艺中的电镀及化学机械抛光\n工艺建模与仿真\n并行EDA算法研究：基于多核、集群系统、GPU的多平台并行EDA算法研究\n模拟电路设计、数字电路设计',
        '教育背景': '复旦大学，半导体物理与半导体器件物理学，博士',
        '学术经历': '2008年01月-2012年12月复旦大学专用集成电路与系统国家重点实验室主任\n2003年09月-2003年11月荷兰TuDelft大学微电子系，客座教授\n2002年09月-2002年11月美国德州A&M大学电机系，客座教授\n2001年12月-至今复旦大学微电子系，教授\n2000年07月-2000年10月美国德州大学达拉斯分校，访问学者\n1999年06月-2001年11月复旦大学电子工程系，副教授\n1998年07月-1999年01月美国北卡大学电机系，访问科学家\n1997年07月-1999年05月复旦大学电子工程系，讲师',
        '荣誉称号': '全国五一巾帼标兵，2015\n上海市优秀学科带头人，2013\n上海市五一劳动奖章，2012\n国家杰出青年基金获得者，2011\n享受政府特殊津贴专家，2009\n新中国成立以来上海百位杰出女教师，2009\n“全国三八红旗手”，2008\n“上海领军人才”，2007\n“上海市三八红旗手标兵”，2006\n上海市第二届“IT青年十大新锐”，2003\n教育部“跨世纪优秀人才培养计划”基金获得者，2002\n教育部首批“高等学校骨干教师资助计划”优秀骨干教师，2002\n科研获奖：\nINTEGRATION, the VLSI Journal最佳论文奖，2018\nIEEE UEMCON国际会议最佳论文奖，2017\nIEEE/ACM Design Automation Conference（DAC）最佳论文提名，2017\nIEEE/ACM Design, Automation and Test in Europe Conference（DATE）最佳论文提名，2017\nIEEE/ACM Asia and South Pacific Design Automation Conference（ASP-DAC）最佳论文提名，2017\nIEEE/ACM International Conference on Computer-Aided Design（ICCAD）最佳论文提名，2017\n上海市自然科学牡丹奖，2014\nIEEE/ACM Design Automation Conference（DAC）最佳论文提名，2013\n第十届中国青年女科学家奖，2013\n上海市自然科学一等奖，2012\n北京市科学技术奖二等奖，2007\n教育部科技进步二等奖，2006\n中国电子学会电子信息科学技术一等奖，2005'
    }
    """
    window11 = soup.find("div", frag = "窗口11")
    if (not window11) or (not window11.contents):
        # 例如[曹颢仪](https://icmne.fudan.edu.cn/2c/a4/c48925a732324/page.htm)老师，window11 元素里是空的
        return {}
    wp_articlecontent = window11.contents[0]

    result = {}
    title = ""
    contents = []
    for mso_normal in wp_articlecontent.children:
        # print(f"{title=}, {contents=}"[:100])
        first_sub_tag = mso_normal.contents[0]
        content = ""
        if first_sub_tag.name == "strong":
            # title
            if title:
                result[title] = sep.join(contents)
            contents.clear()
            title = ''.join([string.strip(":： ") for string in extract_strings(first_sub_tag)])
            # body
            for sub_tag in mso_normal.contents[1:]:
                content += "".join(extract_strings(sub_tag)).strip(":： ")
        else:
            # body
            content = ''.join([string.replace("\xa0", " ").strip() for string in extract_strings(mso_normal)])
        if content:
            contents.append(content)

    if title:
        result[title] = sep.join(contents)

    return result


def parse_data(text: str) -> Dict[str, str]:
    """
    从响应的文本中提取数据。

    Params:

    - text: page() 或 async_page() 返回的结果。

    Return like:

        {
            'name': '曾璇',
            'academic_title': '教授、博士生导师',
            'email': 'xzeng@fudan.edu.cn',
            'research_areas': '集成电路设计自动化\n模拟电路设计自动化：包括电路模拟，模拟电路的行为级建模及模拟，模拟电路版图设计自动化\n高速互连电路分析和综合，包括互连线参数提取、互连线模型降阶、高速时钟设计\n可制造性设计研究，包括工艺偏差下的电路模拟、统计静态时序分析、带参数模型降阶算法；光刻仿真、铜互连工艺中的电镀及化学机械抛光\n工艺建模与仿真\n模拟电路设计、数字电路设计',
            'educational_background': '复旦大学，半导体物理与半导体器件物理学，博士',
            'homepage': 'http://homepage.fudan.edu.cn/xuanzeng/',
            'address': '复旦大学张江校区微电子楼329室',
            'phone': '51355224',
            'image_url': '/_upload/article/images/0e/fe/dd5852dc42f5ab32679b0539d706/fa75ffe4-e5de-48d6-8377-b81533fd951a.jpg'
        }

    对各字段的解释：

    - `name`: 姓名。
    - `academic_title`: 职称。
    - `email`: 电子邮箱地址。
    - `research_areas`: 研究方向。
    - `educational_background`: 教育背景。
    - `homepage`: 个人网址。
    - `address`: 办公地点。
    - `phone`: 电话。
    - `image_url`: 头像图片 URL 。
    """
    if not isinstance(text, str):
        raise TypeError(f"`text` should be a `str`, but got `{type(text).__name__}`")

    soup = BeautifulSoup(text, 'html.parser')

    # 姓名
    name = soup.find('div', class_='arti_title').get_text(strip = True)

    # 职称
    academic_title = "".join([i.get_text(strip = True) for i in soup.find_all('span', class_='zcbt')]).rstrip("、")

    # 电子邮箱地址
    email = soup.find('span', class_='t4').get_text(strip = True)

    # 研究方向 和 教育背景
    window11_content = _extract_window11(soup)
    research_areas = window11_content["研究方向"] if ("研究方向" in window11_content) else ""
    educational_background = window11_content["教育背景"] if ("教育背景" in window11_content) else ""

    # 个人网址
    homepage_match = re.search(r"<span.*?>个人网址[：:]?<\/span><span.*?>(.*?)<\/span>", text)
    homepage = homepage_match.group(1).strip() if homepage_match else ""

    # 办公地点
    address = soup.find('span', class_='t6').get_text(strip = True)

    # 电话
    phone = soup.find('span', class_='t2').get_text(strip = True)

    # 头像图片的 URL
    image_url = soup.find('div', class_='news_imgs').find('img')['src']

    return {
        "name"           : name,
        "academic_title" : academic_title,
        "email"          : email,
        "research_areas" : research_areas,
        "educational_background": educational_background,
        "homepage"       : homepage,
        "address"        : address,
        "phone"          : phone,
        "image_url"      : image_url,
    }
