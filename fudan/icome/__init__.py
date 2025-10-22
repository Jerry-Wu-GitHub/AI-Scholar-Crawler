"""
智能材料与未来能源创新学院 https://icome.fudan.edu.cn/49292/list.htm

注意，在上述网站上，有102名教师，但实际爬取到91位，因为有11名教师（贾波、张昕、肖倩、杨立伟、唐碧、刘惠普、徐锲、钟国泰、钱再波、仝洁、付慧英）的链接类似这样：
```html
<li name="jiab"><a href="javascript:void(0);" target="_self" title="贾波">贾波</a></li>
```
只有姓名信息，其他啥也没有。
"""

college_name = "智能材料与未来能源创新学院"

domain = "icome.fudan.edu.cn"

base_urls = {
    "http" : f"http://{domain}",
    "https": f"https://{domain}",
}

base_url = base_urls["https"]

site_id = "1078"
