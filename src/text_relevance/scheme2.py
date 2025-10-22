"""
通过计算两段文字的余弦相似度来反映相关性。

此方案可以很好地计算中英文混搭的文本。
"""

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # 清华镜像加速模型下载
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"  # 禁用符号链接警告

from sentence_transformers import SentenceTransformer, util

from config.constants import CROSS_LANGUAGE_MODEL


# 加载模型
model = SentenceTransformer("xlm-r-bert-base-nli-stsb-mean-tokens") # 首次加载会从网上下载，耗时较长
print("跨语言模型加载完成")


def text_relevance(text1: str, text2: str) -> float:
    """
    计算两段中文文本的相关性（余弦相似度）
    
    Params:

    - `text1`: 第一段文本。
    - `text2`: 第二段文本。
    
    Return:
    
    - 相关性分数（0~1之间，值越高相关性越强）。
    """
    emb = model.encode([text1, text2], convert_to_tensor = True)
    return util.cos_sim(emb[0], emb[1]).item()


# 相关性阈值，高于这个值可以认为有较强的相关性
# This value was calculated using calculate_stheme2_threshold.py.
RELEVANCE_THRESHOLD: float = 0.4216

# 分类准确率
ACCURACY = 0.8263
