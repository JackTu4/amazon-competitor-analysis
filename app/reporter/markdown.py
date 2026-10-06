from pathlib import Path
def generate_markdown(data):
    markdown=f"""
#亚马逊竞品分析报告
##产品信息
目标产品:
{data.target_product.product.name}
竞品:
{data.competitor.product.name}

##评分
目标产品评分:
{data.target_product.rating}
竞品评分:
{data.competitor.rating}

##分析总结
暂无总结
    """
    return markdown
def save_report(content):
    path=Path("reports/report.md")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(
        content,
        encoding="utf-8",
    )
    return path