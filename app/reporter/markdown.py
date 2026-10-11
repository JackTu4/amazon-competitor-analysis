from pathlib import Path
def display(value):
    """将缺失的数据统一显示为暂无数据。"""
    if value is None or value == "":
        return "暂无数据"
    return str(value)
def format_product(title, item):
    """生成单个产品的详细信息。"""
    product = item.product
    price = item.price
    if price is not None:
        price_text = (
            f"{display(price.amount)} "
            f"{display(price.currency)}"
        )
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
- 价格：{price_text}
- 评分：{display(item.rating)}
- 评论数量：{display(item.reviews)}

### 核心卖点
{bullet_text}
"""
def generate_markdown(data):
    """生成亚马逊竞品分析报告。"""
    target = data.target_product
    competitor = data.competitor
    price_difference = display(data.price_difference)
    summary = data.summary or "当前数据不足，无法形成可靠总结"
    markdown = f"""# 亚马逊竞品分析报告
    
## 一、产品信息
{format_product("目标产品", target)}
{format_product("竞品", competitor)}

## 二、核心指标对比

| 对比指标 | 目标产品 | 竞品 |
|---|---|---|
| 产品名称 | {display(target.product.name)} | {display(competitor.product.name)} |
| 品牌 | {display(target.product.brand)} | {display(competitor.product.brand)} |
| 价格 | {display(target.price.amount) if target.price else "暂无数据"} | {display(competitor.price.amount) if competitor.price else "暂无数据"} |
| 评分 | {display(target.rating)} | {display(competitor.rating)} |
| 评论数量 | {display(target.reviews)} | {display(competitor.reviews)} |

## 三、价格差异
{price_difference}

注：如果两款产品的价格币种不同，不能直接将价格数值相减。

## 四、竞品分析总结
{summary}


## 五、数据说明
本报告依据 Agent 实际返回的数据生成。
未获取到的信息标记为“暂无数据”，不代表该产品不存在相关信息。
"""
    return markdown

def save_report(content):
    path = Path("reports/report.md")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(content, encoding="utf-8")
    return path
