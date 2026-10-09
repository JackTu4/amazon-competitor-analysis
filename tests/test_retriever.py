from app.rag.retriever import retrieve
def test_retrieve():
    results = retrieve(
        "huadisk 的读取速度是多少？",
        top_k=3
    )
    assert results, "没有检索到任何结果"
    for index, item in enumerate(results, start=1):
        print(f"\n第 {index} 条结果")
        print("相似度：", round(item["score"], 4))
        print("来源：", item["source"])
        print("内容：", item["text"])
    assert all("text" in item for item in results)
    assert all("source" in item for item in results)