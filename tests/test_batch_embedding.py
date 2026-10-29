import pytest

pytestmark = pytest.mark.llm

from pathlib import Path
from app.rag.loader import load_document
from app.rag.chunker import split_text
from app.rag.embedding import get_embedding
from app.rag.vector_store import save_vectors, load_vectors
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "app" / "data" / "knowledge"
def test_batch_embedding():
    # 1. 读取所有产品资料
    documents = load_document(str(KNOWLEDGE_DIR))
    assert documents, "没有读取到任何产品资料"
    # 2. 将文档切分成 Chunk，并保留来源
    all_chunks = []
    for document in documents:
        chunks = split_text(
            document["text"],
            chunk_size=200,
            overlap=30
        )
        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "source": document["source"]
            })
    print("读取文档数：", len(documents))
    print("Chunk 总数：", len(all_chunks))
    embedded_chunks = []
    for index, chunk in enumerate(all_chunks):
        vector = get_embedding(chunk["text"])
        embedded_chunks.append({
            "text": chunk["text"],
            "source": chunk["source"],
            "embedding": vector
        })
        print(
            f"完成 {index + 1}/{len(all_chunks)}，"
            f"向量维度：{len(vector)}"
        )
    assert len(embedded_chunks) == len(all_chunks)
    assert all(item["embedding"] for item in embedded_chunks)
    save_vectors(embedded_chunks)
    saved_chunks = load_vectors()
    assert len(saved_chunks) == len(embedded_chunks)
    print("重新读取的 Chunk 数：", len(saved_chunks))
    print("本地向量持久化测试成功！")
    print("成功向量化的 Chunk 数：", len(embedded_chunks))
    print("第一个 Chunk 的来源：", embedded_chunks[0]["source"])
    print("第一个 Chunk 的向量维度：",
              len(embedded_chunks[0]["embedding"]))


