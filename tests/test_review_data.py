
from types import SimpleNamespace
from unittest.mock import patch

from app.agent.agent import competitor_agent


def make_response(tool_calls=None, content=None):
    """构造模拟的 LLM 响应。"""
    message = SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )


def make_tool_call(name, arguments, call_id="call_test"):
    """构造模拟的工具调用。"""
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        ),
    )


def test_target_asin_is_used():
    target_asin = "B0D1R7HDJF"

    knowledge_call = make_tool_call(
        "search_knowledge",
        '{"query": "目标商品规格"}',
        "call_knowledge",
    )

    review_call = make_tool_call(
        "analyze_product_reviews",
        '{"asin": "B0D1R7HDJX"}',  # 故意传入错误 ASIN
        "call_review",
    )

    final_json = """
    {
        "target_product": {
            "product": {
                "name": "测试目标商品",
                "title": "测试目标商品 256GB SSD",
                "asin": "B0D1R7HDJF"
            }
        },
        "competitor": {
            "product": {
                "name": "测试竞品",
                "title": "测试竞品 256GB SSD"
            }
        }
    }
    """

    with patch(
        "app.agent.agent.client.chat.completions.create",
        side_effect=[
            make_response([knowledge_call]),
            make_response([review_call]),
            make_response(content=final_json),
        ],
    ), patch(
        "app.agent.agent.search_knowledge",
        return_value={"results": []},
    ), patch(
        "app.agent.agent.analyze_product_reviews_tool",
        return_value={
            "total_reviews": 3,
            "average_rating": 4.3,
            "pain_points": [],
            "positive_aspects": [],
            "improvement_suggestions": [],
            "summary": "模拟测试",
        },
    ) as mock_review:

        competitor_agent(
            target_product="测试目标商品 256GB SSD",
            competitor="测试竞品 256GB SSD",
            target_asin=target_asin,
        )

        mock_review.assert_called_once_with(
            asin=target_asin
        )

    print("测试通过：评论分析工具使用了程序传入的目标 ASIN。")


if __name__ == "__main__":
    test_target_asin_is_used()
