import pytest

pytestmark = pytest.mark.llm

from app.rag.qa import answer_question
def test_answer_question():
    question = "huadisk 的读取速度是多少？"
    answer = answer_question(question)
    print("\n用户问题：", question)
    print("\nRAG 回答：", answer)
    assert isinstance(answer, str)
    assert answer.strip(), "模型没有返回回答"
