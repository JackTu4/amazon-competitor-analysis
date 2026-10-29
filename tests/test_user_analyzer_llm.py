import pytest

pytestmark = pytest.mark.llm


import json
from pathlib import Path

from app.models.review import Review
from app.analyzers.user_analyzer import analyze_review_sentiment


def test_analyze_saved_reviews():
    # 定位项目根目录
    project_root = Path(__file__).resolve().parents[1]

    # 读取之前保存的 Amazon 评论
    data_file = (
        project_root
        / "app"
        / "data"
        / "reviews"
        / "huadisk_reviews.json"
    )

    assert data_file.exists(), f"评论文件不存在：{data_file}"

    with data_file.open("r", encoding="utf-8") as f:
        raw_reviews = json.load(f)

    # 原始字典 -> Review 模型对象
    reviews = [
        Review.model_validate(item)
        for item in raw_reviews
    ]

    # 调用 LLM 分析
    result = analyze_review_sentiment(reviews)

    # 打印结构化分析结果
    print(result.model_dump_json(indent=2))

    assert result.total_reviews == len(reviews)
    assert isinstance(result.pain_points, list)
    assert isinstance(result.positive_aspects, list)
    assert isinstance(result.improvement_suggestions, list)
    assert isinstance(result.summary, str)
