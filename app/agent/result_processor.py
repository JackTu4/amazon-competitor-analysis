from app.models.review_analysis import ReviewAnalysis

def attach_review_analysis(result, review_data):
    """将目标商品评论分析结果写入最终竞品分析模型。"""

    if not review_data:
        return result

    # 如果最终结果是错误字典，就不进行合并
    if isinstance(result, dict):
        return result

    # 将评论分析字典转换为 ReviewAnalysis 对象
    review_result = ReviewAnalysis.model_validate(review_data)

    # 写入目标商品的评论分析字段
    result.target_product.review_analysis = review_result

    return result
