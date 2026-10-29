from pathlib import Path

from app.rag.chunker import split_text
from app.rag.loader import load_document
# 获取项目根目录：scripts/manual 的上两级目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# 拼接知识库目录
knowledge_dir = PROJECT_ROOT / "app" / "data" / "knowledge"
documents = load_document(str(knowledge_dir))
print(f"读取到 {len(documents)} 份资料")
for document in documents:
    chunks=split_text(
        document["text"],
        chunk_size=35,
        overlap=30,
    )
    document["chunks"]=chunks
    print("\n来源：", document["source"])
    print("切分数量",len(chunks))
    print("Chunk 数量：", len(chunks))
    print("第一个 Chunk 长度：", len(chunks[0]))
    print("第二个 Chunk 长度：", len(chunks[1]))
    print(document["text"][:1000000])
