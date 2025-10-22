"""
智能机器人与先进制造创新学院 https://ciram.fudan.edu.cn/cslm/list.htm

注意：该院系的老师的个人页面是格式不一的，无法爬取 profile 字段。
"""

college_name = "智能机器人与先进制造创新学院"

domain = "ciram.fudan.edu.cn"

base_urls = {
    "http" : f"http://{domain}",
    "https": f"https://{domain}",
}

base_url = base_urls["https"]

site_id = "1083"
