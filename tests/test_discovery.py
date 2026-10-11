import sys
from pathlib import Path
# 将项目根目录加入 Python 模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from app.agent.competitor_discovery import discover_candidates
if __name__ == "__main__":
    target_product = input("请输入目标产品：")
    candidates = discover_candidates(target_product)
    print("\n========== 候选网页 ==========")
    for index, item in enumerate(candidates, start=1):
        print(f"\n候选 {index}")
        print("搜索词：", item["search_query"])
        print("标题：", item["title"])
        print("网址：", item["url"])
        print("摘要：", item["content"])
