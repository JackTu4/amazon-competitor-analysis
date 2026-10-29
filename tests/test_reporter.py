"""Markdown 报告生成的单元测试，不依赖外部服务。"""

from app.models.competitor import (
    CompetitorAnalysis,
    ProductAnalysis,
)
from app.models.extraction import Product
from app.reporter.markdown import generate_markdown


def make_product(name, brand, rating, reviews):
    return ProductAnalysis(
        product=Product(
            name=name,
            title=f"{name} 产品标题",
            asin="B00TEST000",
            brand=brand,
        ),
        bullet_points=["高速读写", "NVMe 接口"],
        rating=rating,
        reviews=reviews,
        price=None,
    )


def test_generate_markdown():
    target = make_product("huadisk", "HUADISK", 4.5, 200)
    competitor = make_product("sumsam", "Samsung", 4.7, 5000)

    analysis = CompetitorAnalysis(
        target_product=target,
        competitor=competitor,
        price_difference=None,
        summary="huadisk价格更低,sumsam影响力更强",
    )

    # generate_markdown 的入参是 {"analyses": [...]} 结构
    result = generate_markdown({
        "analyses": [{"analysis": analysis}],
    })

    assert "# 亚马逊竞品分析报告" in result
    assert "huadisk" in result
    assert "sumsam" in result
    assert "4.5" in result
    assert "价格更低" in result
    # 缺失数据统一显示为暂无数据
    assert "暂无数据" in result


def test_generate_markdown_without_valid_analysis():
    result = generate_markdown({"analyses": []})

    assert "# 亚马逊竞品分析报告" in result
    assert "没有成功分析的竞品" in result


def test_generate_markdown_surfaces_failed_competitor():
    """失败竞品不能静默消失，要写进报告。"""

    target = make_product("huadisk", "HUADISK", 4.5, 200)
    competitor = make_product("sumsam", "Samsung", 4.7, 5000)

    analysis = CompetitorAnalysis(
        target_product=target,
        competitor=competitor,
        price_difference=None,
        summary="价格更低",
    )

    result = generate_markdown({
        "analyses": [
            {"competitor_name": "sumsam", "analysis": analysis},
            {
                "competitor_name": "坏竞品",
                "analysis": {
                    "error": "timeout",
                    "message": "评论分析超时",
                },
            },
        ],
    })

    assert "未完成分析的竞品" in result
    assert "坏竞品" in result
    assert "评论分析超时" in result


def test_generate_markdown_all_competitors_failed():
    result = generate_markdown({
        "analyses": [
            {
                "competitor_name": "坏竞品",
                "analysis": {"error": "boom"},
            },
        ],
    })

    assert "没有成功分析的竞品" in result
    assert "坏竞品" in result
    assert "boom" in result
