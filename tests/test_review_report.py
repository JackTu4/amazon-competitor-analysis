
from app.agent.competitor_verifier import find_target_asin


def test_find_target_asin():
    """测试能否根据商品名称搜索并提取 ASIN。"""

    result = find_target_asin("HuaDisk 256GB NVMe SSD")

    print("\n测试结果：", result)

    if result and result.get("asin"):
        print("找到了候选 ASIN：", result["asin"])
        print("商品标题：", result["title"])
        print("商品链接：", result["url"])
    else:
        print("没有找到有效 ASIN")


if __name__ == "__main__":
    test_find_target_asin()
