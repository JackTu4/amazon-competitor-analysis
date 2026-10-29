"""不花钱的评分自检：只验证纯函数，不连数据库、不调外部 API。

用法：
    python -m evals.selftest
"""

from __future__ import annotations

import sys

from evals import framework


def test_target_checks() -> None:
    expected = {
        "target_asin": "B0TARGET01",
        "brand": "Samsung",
        "price": 49.99,
        "rating": 4.6,
        "reviews": 12000,
    }
    target = {
        "asin": "B0TARGET01",
        "brand": "Samsung Electronics",
        "price": 51.0,
        "rating": 4.6,
        "reviews": 12500,
    }

    checks = framework.target_field_checks(expected, target)

    assert all(value is True for value in checks.values()), checks
    assert framework.rate_checks(checks) == 1.0

    wrong = framework.target_field_checks(expected, dict(target, asin="B0WRONG001"))
    assert wrong["asin"] is False
    assert framework.rate_checks(wrong) == 0.8

    # 预期值留空 -> 不参与计分
    empty = framework.target_field_checks(
        {
            "target_asin": "",
            "brand": "",
            "price": None,
            "rating": None,
            "reviews": None,
        },
        target,
    )
    assert all(value is None for value in empty.values()), empty
    assert framework.rate_checks(empty) is None

    # 目标商品没落库 -> 已填的字段全部判错
    assert framework.target_field_checks(expected, None)["asin"] is False


def test_competitors() -> None:
    expected = {"category_keywords": ["ssd", "nvme"]}
    target = {"asin": "B0TARGET01", "brand": "Samsung"}

    good = {
        "name": "Crucial P3",
        "title": "Crucial P3 1TB NVMe SSD",
        "asin": "B0COMPA001",
        "brand": "Crucial",
        "price": 45.0,
        "rating": 4.5,
        "reviews": 8000,
        "sources": [{"url": "https://www.amazon.com/dp/B0COMPA001"}],
    }
    same_brand = dict(good, asin="B0COMPA002", brand="Samsung Electronics")
    broken = {"name": "Broken", "title": "Broken", "asin": None, "brand": None}
    off_category = dict(good, asin="B0COMPA003", title="Sony headphones", brand="Sony")

    score = framework.score_competitors(
        [good, same_brand, broken, off_category],
        target,
        expected,
    )

    # 只取前 3 个竞品计分
    assert len(score["details"]) == 3, score["details"]
    assert score["valid_count"] == 1, score["valid_count"]
    assert score["details"][0]["rate"] == 1.0
    assert score["details"][1]["checks"]["different_brand"] is False
    assert score["details"][2]["checks"]["asin_format"] is False

    assert framework.score_competitors([], target, expected) == {
        "rate": 0.0,
        "valid_count": 0,
        "details": [],
    }


def test_completeness() -> None:
    assert framework.completeness([]) == 0.0

    half = [{"name": "a", "title": "b"}]
    assert abs(framework.completeness(half) - 2 / 8) < 1e-9


def test_cost() -> None:
    usage = {
        "prompt_tokens": 1_000_000,
        "completion_tokens": 500_000,
        "embedding_tokens": 2_000_000,
        "tavily_calls": 10,
        "brightdata_jobs": 4,
    }
    pricing = {
        "llm_input_per_1m": 1,
        "llm_output_per_1m": 2,
        "embedding_per_1m": 0.1,
        "tavily_per_search": 0.008,
        "brightdata_per_job": 0.0015,
    }

    cost = framework.compute_cost(usage, pricing)

    assert cost["llm"] == 2.0, cost
    assert cost["embedding"] == 0.2, cost
    assert cost["external"] == 0.086, cost
    assert cost["total"] == 2.286, cost
    assert framework.compute_cost({}, {})["total"] == 0.0


def test_cases_file() -> None:
    cases = framework.load_cases()

    assert len(cases) == 10, len(cases)
    assert [case["id"] for case in cases] == [
        f"case-{index:02d}" for index in range(1, 11)
    ]


def main() -> int:
    tests = [
        test_target_checks,
        test_competitors,
        test_completeness,
        test_cost,
        test_cases_file,
    ]

    for test in tests:
        test()
        print(f"  ok  {test.__name__}")

    print("评分逻辑自检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())