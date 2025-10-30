import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time

from fudan.spider import async_general_information
from config.constants import ALL_DATA_FILE_PATH, INFORMATION_FILE_PATH, FILE_ENCODING, MAX_WORKERS
from exlibrisgroup.spider import Session
# from exlibrisgroup.hosted.fudan_primo.primo_library.libweb.webservices import guestJwt, pnxs


if __name__ == '__main__':
    obtain_general_data: bool = True
    obtain_paper_data: bool = True

    if obtain_general_data:
        # 爬取基本数据
        start_time = time.time()
        print("开始爬取基本数据。")
        teacher_infos = asyncio.run(async_general_information())
        end_time = time.time()
        print(f"基本信息请求全部完成，耗时 {end_time - start_time:.2f} 秒。")
        with open(INFORMATION_FILE_PATH, mode = "w", encoding = FILE_ENCODING) as file:
            for teacher_info in teacher_infos:
                json.dump(teacher_info, file, ensure_ascii = False)
                file.write("\n")

    if (not obtain_general_data) and obtain_paper_data:
        # 从 INFORMATION_FILE_PATH 中读出基本数据
        teacher_infos = []
        with open(INFORMATION_FILE_PATH, mode = 'r', encoding = FILE_ENCODING) as file:
            for line in file.readlines():
                line = line.strip()
                if line:
                    teacher_infos.append(json.loads(line))

    if obtain_paper_data:
        # 爬取论文数据
        start = time.time()
        print("开始爬取论文数据。")
        with ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
            session = Session(limit = 100, executor = executor)
            paper_infos = asyncio.run(session.async_paper_informations(teacher_infos))
        print(f"论文数据爬取完毕，耗时 {time.time() - start:.2f} 秒。")
        with open(ALL_DATA_FILE_PATH, mode = 'w', encoding = FILE_ENCODING) as file:
            for paper_info in paper_infos:
                json.dump(paper_info, file, ensure_ascii=False)
                file.write("\n")

    # # Test
    # token = "eyJraWQiOiJwcmltb0V4cGxvcmVQcml2YXRlS2V5LUZEVSIsImFsZyI6IkVTMjU2In0.eyJpc3MiOiJQcmltbyIsImp0aSI6IiIsImNtanRpIjpudWxsLCJleHAiOjE3NjE5MTY4MTgsImlhdCI6MTc2MTgzMDQxOCwidXNlciI6ImFub255bW91cy0xMDMwXzEzMjAxOCIsInVzZXJOYW1lIjpudWxsLCJ1c2VyR3JvdXAiOiJHVUVTVCIsImJvckdyb3VwSWQiOm51bGwsInViaWQiOm51bGwsImluc3RpdHV0aW9uIjoiRkRVIiwidmlld0luc3RpdHV0aW9uQ29kZSI6IkZEVSIsImlwIjoiMTM5LjIyNy4yNDQuMTUiLCJwZHNSZW1vdGVJbnN0IjpudWxsLCJvbkNhbXB1cyI6ImZhbHNlIiwibGFuZ3VhZ2UiOiJ6aF9DTiIsImF1dGhlbnRpY2F0aW9uUHJvZmlsZSI6IiIsInZpZXdJZCI6ImZkdSIsImlsc0FwaUlkIjpudWxsLCJzYW1sU2Vzc2lvbkluZGV4IjoiIiwiand0QWx0ZXJuYXRpdmVCZWFjb25JbnN0aXR1dGlvbkNvZGUiOiJGRFUifQ.DSVdzgGYH1GJ9YdgF_tHdJ-eriujZR6p9WjL46xDr0nBgYCts80PVY_aBSFsmgv80GonZRAdLgmArElMa5grgw"
    # token = guestJwt("fdu")
    # data = pnxs(token, "阚海斌", 10, "fdu")
    # with open("data/search_result.jsonl", mode = "w", encoding = "utf-8") as file:
    #     for line in data:
    #         json.dump(line, file, ensure_ascii = False)
    #         file.write("\n")
