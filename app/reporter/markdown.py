import logging
import uuid
from pathlib import Path

from app.models.competitor import CompetitorAnalysis

logger = logging.getLogger(__name__)
def display(value):
    """将缺失的数据统一显示为暂无数据。"""
    if value is None or value == "":
        return "暂无数据"
    return str(value)
def format_product(title, item):
    """生成单个产品的详细信息。"""
    product = item.product
    price = item.price
    amount = price.amount if price is not None else None
    currency = price.currency if price is not None else None
    if amount is not None or currency is not None:
        price_text = f"{display(amount)} {display(currency)}".strip()
    else:
        price_text = "暂无数据"
    bullets = item.bullet_points or []
    if bullets:
        bullet_text = "\n".join(
            f"- {point}" for point in bullets
        )
    else:
        bullet_text = "- 暂无数据"
    return f"""
## {title}
- 产品名称：{display(product.name)}
- 产品标题：{display(product.title)}
- ASIN：{display(product.asin)}
- 品牌：{display(product.brand)}
- 容量：{display(product.capacity)}
- 接口：{display(product.interface)}
- 外形规格：{display(product.form_factor)}
- 型号：{display(product.model)}
- 价格：{price_text}
- 评分：{display(item.rating)}
- 评论数量：{display(item.reviews)}

### 核心卖点
{bullet_text}
"""

def format_review_analysis(review_analysis):
    """将评论分析结果格式化为 Markdown。"""


    if review_analysis is None:
        return (
            "### 用户评论分析\n"
            "- 当前没有可用的评论分析数据"
        )

    def format_list(title, items):
        items = items or []
        if not items:
            return f"#### {title}\n- 暂无数据"

        lines = "\n".join(f"- {item}" for item in items)
        return f"#### {title}\n{lines}"

    return "\n\n".join([
        "### 用户评论分析",
        f"- 分析评论数量：{display(review_analysis.total_reviews)}",
        f"- 评论平均评分：{display(review_analysis.average_rating)}",
        format_list("用户痛点", review_analysis.pain_points),
        format_list("产品优点", review_analysis.positive_aspects),
        format_list("改进建议", review_analysis.improvement_suggestions),
        f"#### 评论分析总结\n{display(review_analysis.summary)}",
    ])

def _comparison_table(target, competitor):
    """目标产品与单个竞品的核心指标对比表。"""
    return (
        "| 对比指标 | 目标产品 | 竞品 |\n"
        "|---|---|---|\n"
        f"| 产品名称 | {display(target.product.name)} | {display(competitor.product.name)} |\n"
        f"| 品牌 | {display(target.product.brand)} | {display(competitor.product.brand)} |\n"
        f"| 价格 | {display(target.price.amount) if target.price else '暂无数据'} | {display(competitor.price.amount) if
        competitor.price else '暂无数据'} |\n"
        f"| 评分 | {display(target.rating)} | {display(competitor.rating)} |\n"
        f"| 评论数量 | {display(target.reviews)} | {display(competitor.reviews)} |\n"
        f"| 容量 | {display(target.product.capacity)} | {display(competitor.product.capacity)} |\n"
        f"| 接口 | {display(target.product.interface)} | {display(competitor.product.interface)} |\n"
        f"| 外形规格 | {display(target.product.form_factor)} | {display(competitor.product.form_factor)} |\n"
        f"| 型号 | {display(target.product.model)} | {display(competitor.product.model)} |\n"
    )


def generate_markdown(data):
    """生成亚马逊竞品分析报告（支持多个竞品）。"""
    analyses = data.get("analyses", [])
    valid = []
    for item in analyses:
        analysis = item.get("analysis")
        if isinstance(analysis, dict):
            try:
                analysis = CompetitorAnalysis(**analysis)
            except Exception as e:
                logger.warning(
                    "竞品分析结果无效，跳过该竞品。竞品名称：%s，原因：%s",
                    item.get("competitor_name", "未知"),
                    e,
                )
                continue

        if isinstance(analysis, CompetitorAnalysis):
            valid.append(analysis)

    if not valid:
        return "# 亚马逊竞品分析报告\n\n当前没有成功分析的竞品，无法生成对比报告。\n"

    target = next(
        (
            item.target_product
            for item in valid
            if item.target_product.review_analysis is not None
        ),
        valid[0].target_product,
    )
    parts = [
        "# 亚马逊竞品分析报告",
        "",
        "## 一、目标产品",
        format_product("目标产品", target),
        format_review_analysis(target.review_analysis),
    ]

    for idx, comp in enumerate(valid, start=1):
        parts.append(f"## 二、竞品 {idx}")
        parts.append(format_product(f"竞品 {idx}", comp.competitor))
        parts.append(f"### 核心指标对比（竞品 {idx}）")
        parts.append(_comparison_table(target, comp.competitor))
        parts.append(f"### 价格差异（竞品 {idx}）")
        parts.append(display(comp.price_difference))
        parts.append("注：如果两款产品的价格币种不同，不能直接将价格数值相减。")
        parts.append(f"### 分析总结（竞品 {idx}）")
        parts.append(comp.summary or "当前数据不足，无法形成可靠总结")

    parts.append("## 三、数据说明")
    parts.append("本报告依据 Agent 实际返回的数据生成。")
    parts.append("未获取到的信息标记为“暂无数据”，不代表该产品不存在相关信息。")
    return "\n\n".join(parts)

def save_report(content,task_id=None):
    if task_id is None:
        task_id=str(uuid.uuid4())
    path=Path("reports")/f"{task_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        content,
        encoding="utf-8"
        )
    return path