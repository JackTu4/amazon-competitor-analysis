import pytest

pytestmark = pytest.mark.llm

from app.tools.knowledge_tool import search_knowledge
def test_search_knowledge():
    result=search_knowledge(
        "KingSpec的产品容量有哪些",
        top_k=3,
    )
    print("\n检索结果:",result)
    assert "query" in result
    assert "results" in result
    for item in result["results"]:
        assert "text" in item
        assert "source" in item
        assert "score" in item