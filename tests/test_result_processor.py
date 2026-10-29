
from app.models.competitor import CompetitorAnalysis
from app.models.review_analysis import ReviewAnalysis
from app.reporter.markdown import generate_markdown


def test_full_review_report():
    review_analysis = ReviewAnalysis(
        total_reviews=3,
        average_rating=4.0,
        pain_points=["安装说明不够清楚"],
        positive_aspects=["价格实惠"],
        improvement_suggestions=["完善安装说明"],
        summary="用户认可价格，但希望改进安装说明。",
    )

    # 使用已有的 CompetitorAnalysis 模型构造模拟数据
    data = {
        "analyses": [
            {
                "analysis": {
                    "target_product": {
                        "product": {
                            "name": "测试目标商品",
                            "title": "Test Target SSD",
                            "asin": "B000000001",
                            "brand": "TestBrand",
                            "capacity": "256GB",
                            "interface": "NVMe",
                            "form_factor": "M.2 2280",
                            "model": "TEST-256",
                        },
                        "bullet_points": [],
                        "rating": 4.0,
                        "reviews": 10,
                        "price": None,
                        "review_analysis": review_analysis.model_dump(),
                    },
                    "competitor": {
                        "product": {
                            "name": "测试竞品",
                            "title": "Test Competitor SSD",
                            "asin": "B000000002",
                            "brand": "OtherBrand",
                            "capacity": "256GB",
                            "interface": "NVMe",
                            "form_factor": "M.2 2280",
                            "model": "OTHER-256",
                        },
                        "bullet_points": [],
                        "rating": 4.2,
                        "reviews": 20,
                        "price": None,
                    },
                    "price_difference": None,
                    "summary": "模拟竞品分析总结。",
                }
            }
        ]
    }

    markdown = generate_markdown(data)

    assert "测试目标商品" in markdown
    assert "用户评论分析" in markdown
    assert "安装说明不够清楚" in markdown
    assert "价格实惠" in markdown
    assert "完善安装说明" in markdown

    print("完整报告生成测试通过！")
