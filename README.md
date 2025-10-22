# Crawl the Information of Fudan Professors

---

## 介绍

本项目用于爬取复旦的老师的基本信息和论文数据。

- 基本信息包括：

    - `person_id` ：该老师的唯一编号。

    - `name` ：该老师的姓名。

    - `college` ：该老师所在的院系。

    - `academic_title` ：该老师的职称。

    - `profile` ：该老师的学位或学习工作经历。

    - `personal_website` ：该老师的个人页面的 URL 。

    - `subject` ：该老师的研究方向。

    - `email` ：该老师的电子邮箱地址。

    - `phone` ：该老师的电话号码。

    示例：

    ```json
    {"person_id": "37168", "name": "阚海斌", "college": "计算与智能创新学院", "academic_title": "教授、博导", "profile": "1999，博士学位，复旦大学数学所", "personal_website": "http://cis.cs.fudan.edu.cn/", "subject": "编码与信息论，密码学与信息安全，计算复杂性", "email": "hbkan@fudan.edu.cn", "phone": ""}
    ```

- 论文数据包括：

    - `person_id` ：该老师的唯一编号。

    - `author_cn` ：该老师的中文姓名。

    - `author_en` ：该老师的英文名，目前一律为空。

    - `author_email` ：该老师的电子邮箱地址。

    - `title_cn` ：该论文的中文标题。

    - `title_en` ：该论文的英文标题，目前一律为空。

    - `keyword_cn` ：该论文的关键词（中文）。

    - `keyword_en` ：该论文的关键词（英文），目前一律为空。

    - `article_info` ：该论文的标题+描述。

    示例：

    ```json
    {"person_id": "37168", "author_cn": "阚海斌", "author_en": "", "author_email": "hbkan@fudan.edu.cn", "title_cn": "基于多分数阶混沌系统的彩色图像加密算法", "title_en": "", "keyword_cn": "分数阶混沌系统；图像置乱；密文交错扩散；混沌加密；彩色图像", "keyword_en": "", "article_info": "基于多分数阶混沌系统的彩色图像加密算法  为了实现对彩色图像信息的有效保护，提出一种像素置乱及密文交错扩散技术相结合的加密算法。首先对3个分数阶混沌系统产生的混沌序列进行优化改进，得到两组不同的性能优良的混沌密钥序列，并将RGB彩色图像转换为由基色分量组成的灰度图像；然后，利用一组改进的混沌密钥序列对该灰度图像的像素位置进行置乱；最后，利用另一组改进的混沌密钥序列对置乱图像进行2轮基色分量之间的密文交错扩散操作，得到加密图像。仿真实验表明，该算法具有足够大的密钥空间，高度的密钥敏感性，较好的像素分布特性，且在抵抗唯密文攻击、差分攻击、选择明文攻击及统计攻击方面都具有良好的性能，可以广泛地应用于多媒体数据的保密通信中。 "}
    ```

以上数据的类型都是字符串（`str`），若缺省，则为空字符串（`""`）。

目前囊括了以下学院的数据：

| **学院**                     | **师资队伍**                                   |
| ---------------------------- | ---------------------------------------------- |
| 计算与智能创新学院           | https://ai.fudan.edu.cn/zzjs_39692/list.htm    |
| 集成电路与微纳电子创新学院   | https://icmne.fudan.edu.cn/apy/list.htm        |
| 智能材料与未来能源创新学院   | https://icome.fudan.edu.cn/49292/list.htm      |
| 智能机器人与先进制造创新学院 | https://ciram.fudan.edu.cn/cslm/list.htm       |
| 未来信息创新学院             | http://www.it.fudan.edu.cn/Data/List/azc       |
| 生物医学工程与技术创新学院   | https://bme-college.fudan.edu.cn/szdw/list.htm |

## 用法

直接运行 `main.py` 即可。

> [!CAUTION]
>
> 运行时，工作目录需要是 `main.py` 所在的目录。

在 `config.constants` 中，用户可以完成个性化的配置。下面是对 `config.constants` 的内容的介绍：

- `COLLEGES` 是每个学院的代号，对应着 `./fudan` 文件夹下的模块名。这个不能改。

- `COMMON_HEADERS` 是发送网络请求时用的请求头的公共部分，默认为：

    ```python
    {
        'accept-language': 'zh-CN,zh;q=0.9',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
    }
    ```

- `CONCURRENCY_NUMBER` ：向同一个 URL 发送请求的最大异步并发数量，默认为 `100` 。

- `MAX_WORKERS` ：线程的最大并发数量，默认为系统的核数。

- `RETRANSMISSION` ：请求失败时，单个请求的最大发送次数。

- `DATA_DIR` ：默认的存放数据的文件夹的路径，默认为 `"./data"` 。

- `FILE_ENCODING` ：文本文件的编码，默认为 `"utf-8"` ，在写入 `all_data.jsonl` 和 `professor_information.jsonl` 时被使用。

- `ALL_DATA_FILE_PATH` ：文件 `all_data.jsonl` 的路径，默认为 `./data/all_data.jsonl` 。

- `INFORMATION_FILE_PATH` ：文件 `professor_information.jsonl` 的路径，默认从环境变量中读取 `INFORMATION_FILE_PATH` 。若找不到该环境变量，则默认设为 `./data/professor_information.jsonl` 。

- `STOPWORDS` ：分词后要剔除的词，用于分词方案1（`scheme1`）。

- `CROSS_LANGUAGE_MODEL` ：向量化文本所用的跨语言模型，用于分词方案2（`scheme2`）。

- `SCHEME` ：计算文本相关性的方案，默认为 `scheme2` 。

## 组成

本项目的核心代码由两部分组成：

- `./fudan` ：该目录下的模块分别用于爬取各学院的老师的基本信息。

    - 对于爬取到的两条 `"name"` 相同的数据，有以下三种情况：

        1. 同一个老师在同一个学院有两个个人页面，其中一个个人页面一般是空的。
        2. 同一个老师在两个不同的学院都有个人页面。
        3. 这就是两个不同的老师，只是重名了而已。

        对情况1、2，会进行数据合并，故最后得到的数据中一般没有两条数据是同一个老师的。具体的去重方法见 [同名处理方法.md](同名处理方法.md) 。

- `./exlibrisgroup` ：用于从图书馆爬取论文数据。

    - 用老师的姓名为关键词进行搜索，会得到多条搜索结果，以下是判断某条搜索结果是否属于该老师的方法：

        1. 判断老师的姓名是否属于该论文的作者。
        2. 计算老师的研究方向（`"subject"`）与该论文的描述（`titile + keywords + description`）的文本相似性（$\in [0, 1]$），若相似性超过阈值，则认为该论文是这位老师写的。

    - 计算文本相似性的方案：

        - `scheme1` ：准确度较低，无法处理中英文混杂的情况，但速度快。
        - `scheme2` ：准确度较高，可以处理中英文混杂的情况，但速度慢。

        由于本项目对时间的要求不高，故优先使用 `scheme2` 。

## 耗时

- 若使用 `scheme1` ，则需要运行大约 400 秒。
- 若使用 `scheme2` ，则需要运行大约一小时。