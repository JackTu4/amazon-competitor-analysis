from app.rag.retriever import retrieve
def search_knowledge(query:str,top_k:int=3)->dict:
    """检索本地亚马逊产品知识库,返回相关文本、来源和相似度"""
    results=retrieve(query,top_k)
    return{
        "query":query,
        "results":[
            {
                "text":item["text"],
                "source":item["source"],
                "score":round(item["score"],4),
            }
            for item in results
        ]
    }