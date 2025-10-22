"""
通过计算两段文字的余弦相似度来反映相关性。

此方案无法较好地计算中英文混搭的文本。
"""

from typing import List

import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config.constants import STOPWORDS


def tokenize(text: str) -> List[str]:
    """
    分词函数，并过滤停用词和空字符。

    Params:

    - `text`: 文本，可以中英文混搭。如：`"编码与信息论，密码学与信息安全，计算复杂性。"`

    Return like:

    ```python
    ['编码', '信息', '信息论', '密码', '密码学', '信息', '信息安全', '安全', '计算', '复杂', '复杂性']
    ```
    """
    words = jieba.cut(text, cut_all = True) # 分词
    return [word for word in words if word.strip() and word not in STOPWORDS] # 去停用词和空字符


def text_relevance(text1: str, text2: str) -> float:
    """
    计算两段中文文本的相关性（余弦相似度）
    
    Params:

    - `text1`: 第一段文本。
    - `text2`: 第二段文本。
    
    Return:
    
    - 相关性分数（0~1之间，值越高相关性越强）。
    """

    # 处理空文本
    if (not text1) or (not text2):
        return 0.0

    # 用TF-IDF将文本转换为向量
    vectorizer = TfidfVectorizer(tokenizer=tokenize)

    # 合并两段文本进行拟合（确保词表一致）
    tfidf_matrix = vectorizer.fit_transform([text1, text2])

    # 计算余弦相似度（返回值范围0~1）
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    return similarity


# 相关性阈值，高于这个值可以认为有较强的相关性
RELEVANCE_THRESHOLD: float = 0.013
