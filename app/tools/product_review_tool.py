from app.analyzers.product_review_pipeline import analyze_product_reviews


def analyze_product_reviews_tool(asin: str) -> dict:
    """采集并分析指定 Amazon 商品的用户评论。"""
    result = analyze_product_reviews(asin)

    return result.model_dump()