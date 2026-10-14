import logging
from app.agent.agent import competitor_agent
from app.reporter.markdown import (generate_markdown,save_report)
from app.workflow.task import Task
from app.agent.competitor_discovery import run_discovery
from app.agent.competitor_verifier import find_target_asin
logger = logging.getLogger(__name__)

def discovery_task(data):
    logger.info("执行自动竞品发现任务")
    target_info = find_target_asin(data["target_product"])
    if not target_info:
        raise ValueError("无法找到目标商品的 ASIN")
    data["target_asin"] = target_info["asin"]

    logger.info("目标商品标题：%s", target_info["title"])
    logger.info("目标商品 ASIN：%s", data["target_asin"])
    result=run_discovery(data["target_product"])
    if hasattr(result,"model_dump"):
        result=result.model_dump()
    logger.info("自动竞品发现完成")
    candidates=result.get("candidates",[])
    if not candidates:
        raise ValueError("自动竞品发现失败：没有找到候选竞品")
    selected = candidates[:5]  # 取前 5 个候选
    data["competitors"] = [
        {
            "name": c.get("product_name"),
            "asin": c.get("asin"),
            "url": c.get("source_url"),
        }
        for c in selected
    ]
    logger.info("自动发现的竞品数量：%s", len(data["competitors"]))
    return data


def analysis_task(data):
    logger.info("执行竞品分析任务")
    target = data["target_product"]
    target_asin = data.get("target_asin")
    logger.info("传入分析流程的目标商品 ASIN：%s", target_asin)
    analyses = []
    for comp in data["competitors"]:    #五组竞品  分析了五个竞品与目标产品的数据
        result = competitor_agent(
            target,
            comp["name"],
            target_asin=target_asin,
        )
        analyses.append({
            "competitor_name": comp["name"],
            "competitor_asin": comp["asin"],
            "competitor_url": comp["url"],
            "analysis": result,  # CompetitorAnalysis 或错误 dict
        })
    return {
        "target_product": target,
        "analyses": analyses,
    }

def report_task(result):
    if isinstance(result, dict) and "error" in result:
        logger.warning("报告生成失败，原因：%s", result["error"])
        return result
    logger.info(
        "交给报告生成器的竞品分析数量：%s",
        len(result.get("analyses", []))
    )
    logger.info("执行报告生成任务")
    markdown = generate_markdown(result)
    path = save_report(markdown)
    return path

workflow_tasks=[
    Task(
        name="discover_competitors",
        func=discovery_task,
    ),
    Task(
        name="competitor_analysis",
        func=analysis_task,
    ),
    Task(
        name="generate_report",
        func=report_task,
    )
]