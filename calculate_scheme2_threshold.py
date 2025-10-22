from concurrent.futures import ThreadPoolExecutor
import csv
import json
import random
from typing import List, Any
from src.text_relevance.scheme2 import text_relevance, model
from sentence_transformers import SentenceTransformer, util
import time
import pandas as pd
import math

ALL_DATA_FILE_PATH = "../data/all_data.jsonl"
INFORMATION_FILE_PATH = "../data/professor_information.jsonl"

from config.constants import MAX_WORKERS

CSV_PATH = "data/paper_scores.csv"


class SolveCounter():
    finished = 0

    @classmethod
    def cal_score(cls, text_pair: List[str]) -> float:
        score = text_relevance(text_pair[0], text_pair[1])
        cls.finished += 1
        if cls.finished % 10 == 0:
            print(f"已完成 {cls.finished} / {sample_size}")
        return score

def batch_relevance_fast(text_pairs):
    """
    批量编码优化：一次性编码所有文本，再计算相似度
    适用于大量文本对场景，效率远高于单对处理
    """

    # 提取所有text1和text2（批量处理）
    all_text1 = [pair[0] for pair in text_pairs]
    all_text2 = [pair[1] for pair in text_pairs]

    # 批量编码（一次调用处理所有文本，利用矩阵并行）
    embeddings1 = model.encode(all_text1, convert_to_tensor=True)  # 形状：(N, 384)
    embeddings2 = model.encode(all_text2, convert_to_tensor=True)  # 形状：(N, 384)

    # 批量计算余弦相似度（逐对计算，利用PyTorch广播机制）
    similarities = util.cos_sim(embeddings1, embeddings2).diag().tolist()  # 取对角线（每个text1与对应text2的相似度）
    results = [round(sim, 4) for sim in similarities]

    return results


def split_by_chunck(data: List[Any], chunk_size: int = 100) -> List[List[Any]]:
    """
    将 data 分成多个小份，每份的大小不超过 chunk_size 。
    """
    result = []
    for i in range(0, len(data), chunk_size):
        result.append(data[i: i + chunk_size])
    return result


def cal_scores():
    teacher_infos = []
    with open(INFORMATION_FILE_PATH, mode = "r", encoding = "utf-8") as file:
        for line in (line.strip() for line in file.readlines()):
            if (line):
                teacher_infos.append(json.loads(line))
    print(f"共有 {len(teacher_infos)} 名教师。")


    paper_infos = []
    with open(ALL_DATA_FILE_PATH, mode = "r", encoding = "utf-8") as file:
        for line in (line.strip() for line in file.readlines()):
            if (line):
                try:
                    paper_infos.append(json.loads(line))
                except Exception as error:
                    continue
    print(f"共有 {len(paper_infos)} 篇论文。")


    id_teacher = {}
    id_paper = {}

    for teacher_info in teacher_infos:
        id = teacher_info["person_id"]
        if not id:
            continue
        if id in id_teacher:
            raise Exception(f"id {id} 重复")
        id_teacher[id] = teacher_info
    print(f"共有 {len(id_teacher)} 名有 id 的教师。")

    for paper_info in paper_infos:
        id = paper_info["person_id"]
        if not id:
            continue
        if id in id_paper:
            id_paper[id].append(paper_info)
        else:
            id_paper[id] = [paper_info]
    print(f"共有 {len(id_paper)} 名教师有有 id 的论文。")

    pos_text_pairs = []
    for (id, teacher_info) in id_teacher.items():
        if not teacher_info.get("subject", ""):
            continue
        for paper_info in id_paper.get(id, []):
            if not paper_info.get("article_info", ""):
                continue
            pos_text_pairs.append((
                teacher_info["subject"],
                paper_info["article_info"]
            ))
    pos_sample_size = len(pos_text_pairs)
    print(f"正样本数量为 {pos_sample_size}")

    # 正负样本比为 1:4
    neg_text_pairs = []
    for _ in range(pos_sample_size * 4):
        teacher_info = {"subject": ""}
        while not teacher_info["subject"]:
            teacher_info = random.choice(teacher_infos)

        paper_info = {"person_id": teacher_info["person_id"], "article_info": ""}
        while (paper_info["person_id"] == teacher_info["person_id"]) or (not paper_info.get("article_info", "")):
            paper_info = random.choice(paper_infos)

        neg_text_pairs.append((
            teacher_info.get("subject", ""),
            paper_info.get("article_info", "") or paper_info.get("title_en", "") or paper_info.get("title_cn", "")
        ))
    neg_sample_size = len(neg_text_pairs)
    print(f"负样本数量为 {neg_sample_size}")

    start_time = time.time()
    pos_sample_size = pos_sample_size
    neg_sample_size = neg_sample_size
    with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
        chunk_size = math.ceil(pos_sample_size / MAX_WORKERS)
        pos_scores = sum(executor.map(batch_relevance_fast, split_by_chunck(pos_text_pairs[:pos_sample_size], chunk_size)), [])
        print(f"正样本处理完成，耗时 {time.time() - start_time:.2f} 秒。")
        chunk_size = math.ceil(neg_sample_size / MAX_WORKERS)
        neg_scores = sum(executor.map(batch_relevance_fast, split_by_chunck(neg_text_pairs[:neg_sample_size], chunk_size)), [])
    
    # pos_scores = batch_relevance_fast(pos_text_pairs[:100])
    # neg_scores = batch_relevance_fast(neg_text_pairs[:100])
    
    total_time = time.time() - start_time
    print(f"总耗时：{total_time:.2f}秒")

    with open(CSV_PATH, mode = "w", encoding = "utf-8", newline = "") as file:
        writer = csv.writer(file)
        for score in pos_scores:
            writer.writerow((score, 1))
        for score in neg_scores:
            writer.writerow((score, 0))


def cal_best_score():
    # 加载数据集
    df = pd.read_csv(CSV_PATH)

    # 重命名列名
    df.columns = ['score', 'class_label']

    # 获取 score 的最小值和最大值
    min_score = df['score'].min()
    max_score = df['score'].max()

    # 初始化最优阈值和最优准确率
    best_threshold = None
    best_accuracy = 0

    # 遍历所有可能的阈值
    for threshold in df['score'].sort_values().unique():
        # 根据阈值进行分类
        predicted_labels = (df['score'] >= threshold).astype(int)

        # 计算准确率
        accuracy = (predicted_labels == df['class_label']).mean()

        # 更新最优阈值和最优准确率
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = threshold

    print(f'最优的 score 阈值为: {best_threshold}')
    print(f'对应的分类准确率为: {best_accuracy}')


if __name__ == '__main__':
    cal_scores()
    cal_best_score()
