import pytest

pytestmark = pytest.mark.llm

from app.analyzers.product_review_pipeline import analyze_product_reviews


def test_analyze_product_reviews():
    result = analyze_product_reviews("B0FFGXYXQV")

    print(result.model_dump_json(indent=2))

    assert result.total_reviews >= 0
    assert isinstance(result.pain_points, list)
    assert isinstance(result.positive_aspects, list)
    assert isinstance(result.improvement_suggestions, list)