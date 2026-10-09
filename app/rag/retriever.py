import math
from app.rag.embedding import get_embedding
from app.rag.vector_store import load_vectors
def cosine_similarity(vector_a:list[float], vector_b:list[float])->float:
    """计算两个向量的余弦相似度"""
    if len(vector_a) != len(vector_b):
        raise ValueError("两个向量长度必须相等！")
    dot_product=sum(
        a*b for a,b in zip(vector_a,vector_b)
    )   #  点积相乘
    norm_a=math.sqrt(sum(a*a for a in vector_a))
    norm_b=math.sqrt(sum(b*b for b in vector_b))
    if norm_a==0 or norm_b==0:
        return 0.0
    return dot_product/(norm_a*norm_b)

def retrieve(query:str,top_k:int=3)->list[dict]:
    """根据问题检索相关的CHUNK."""
    query_vector=get_embedding(query)
    stored_chunks=load_vectors()
    results=[]
    for chunk in stored_chunks:
        score=cosine_similarity(
            query_vector,chunk["embedding"]
        )
        results.append({
            "text":chunk["text"],
            "source":chunk["source"],
            "score":score,
        })
    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )
    return results[:top_k]