import pytest

pytestmark = pytest.mark.llm

from app.agent.agent import competitor_agent
def test_agent_pipeline():
    result=competitor_agent(
        "Huadisk SSD",
        "Samsung SSD"
    )
    print(result)
if __name__ == '__main__':
    test_agent_pipeline()