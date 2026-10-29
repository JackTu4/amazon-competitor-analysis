import pytest

pytestmark = pytest.mark.llm

from app.rag.embedding import get_embedding
def test_get_embedding():
    text = "KingSpec SSD 的读取速度最高可达 2400MB/s。"
    vector = get_embedding(text)
    assert isinstance(vector, list)
    assert len(vector) > 0
    print("向量维度：", len(vector))
    print("向量前 10 个数字：", vector[:10])