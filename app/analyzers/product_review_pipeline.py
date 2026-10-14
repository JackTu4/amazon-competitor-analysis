from app.tools.brightdata_reviews import collect_amazon_reviews
from app.analyzers.user_analyzer import analyze_review_sentiment
from app.models.review_analysis import ReviewAnalysis

def analyze_product_reviews(asin:str)->ReviewAnalysis:
    """自动采集Amazon评论分析用户反馈"""
    #第一步:自动采集评论
    reviews=collect_amazon_reviews(
        asin=asin,
        max_reviews=3
    )

    # 第二步：分析评论
    result = analyze_review_sentiment(reviews)
    return result
