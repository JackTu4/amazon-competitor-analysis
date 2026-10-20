from app.models.review import Review
from app.llm.client import client
from app.models.review_analysis import ReviewAnalysis
import json
from dotenv import load_dotenv
import os
load_dotenv()

def analyze_user_reviews(reviews: list[Review]) -> dict:
    """统计 Amazon 评论，并整理可供后续 LLM 分析的评论内容。"""

    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": None,
            "low_rating_count": 0,
            "high_rating_count": 0,
            "low_rating_reviews": [],
            "high_rating_reviews": [],
        }

    # 1. 统计有效评分
    ratings = [
        review.rating
        for review in reviews
        if review.rating is not None
    ]

    average_rating = (
        round(sum(ratings) / len(ratings), 2)
        if ratings
        else None
    )

    # 2. 筛选差评：评分不高于 3 星
    low_rating_reviews = [
        {
            "rating": review.rating,
            "title": review.review_header,
            "text": review.review_text,
        }
        for review in reviews
        if review.rating is not None and review.rating <= 3
    ]

    # 3. 筛选好评：评分不低于 4 星
    high_rating_reviews = [
        {
            "rating": review.rating,
            "title": review.review_header,
            "text": review.review_text,
        }
        for review in reviews
        if review.rating is not None and review.rating >= 4
    ]

    return {
        "total_reviews": len(reviews),
        "average_rating": average_rating,
        "low_rating_count": len(low_rating_reviews),
        "high_rating_count": len(high_rating_reviews),
        "low_rating_reviews": low_rating_reviews,
        "high_rating_reviews": high_rating_reviews,
    }

def analyze_review_sentiment(
    reviews: list[Review],
    model: str =os.getenv("LLM_MODEL_NAME", "qwen3.7-flash"),
) -> ReviewAnalysis:
    """调用 LLM 分析用户评论中的痛点、优点和改进建议"""
    review_data = [
        {
            "rating": review.rating,
            "title": review.review_header,
            "text": review.review_text,
        }
        for review in reviews
        if review.review_header or review.review_text
    ]
    if not review_data:
        stats = analyze_user_reviews(reviews)

        return ReviewAnalysis(
            total_reviews=stats["total_reviews"],
            average_rating=stats["average_rating"],
            summary="没有足够的评论文本进行语义分析。",
        )

    stats = analyze_user_reviews(reviews)
    prompt = f"""
    请分析以下 Amazon 商品评论。

    请仅依据评论内容，使用中文返回 JSON，字段如下：
    - pain_points：用户明确提到的痛点列表
    - positive_aspects：用户认可的优点列表
    - improvement_suggestions：有评论证据支持的改进建议列表
    - summary：评论整体总结

    要求：
    1. 不要编造评论中没有的信息。
    2. 不要将个别用户的体验夸大成普遍问题。
    3. 如果评论数量较少，要明确说明结论的局限性。
    4. 只返回 JSON，不要附加 Markdown。

    评论统计：
    {json.dumps(stats, ensure_ascii=False)}

    评论内容：
    {json.dumps(review_data, ensure_ascii=False)}
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是严谨的 Amazon 用户评论分析助手。",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("LLM 返回了空的评论分析结果")

    result = json.loads(content)

    # 统计值由 Python 提供，不依赖 LLM 计算
    result["total_reviews"] = stats["total_reviews"]
    result["average_rating"] = stats["average_rating"]

    return ReviewAnalysis.model_validate(result)

