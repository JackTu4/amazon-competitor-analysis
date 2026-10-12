import logging

from app.agent.agent import competitor_agent
from app.reporter.markdown import (generate_markdown,save_report)
from app.workflow.task import Task
from app.agent.competitor_discovery import run_discovery

logger = logging.getLogger(__name__)
def discovery_task(data):
    logger.info("执行自动竞品发现任务")
    result=run_discovery(data["target_product"])
    if hasattr(result,"model_dump"):
        result=result.model_dump()
    logger.info("自动竞品发现完成")
    candidates=result.get("candidates",[])
    if not candidates:
        raise ValueError("自动竞品发现失败：没有找到候选竞品")
    selected=candidates[0]
    data["competitor"]=selected.get("product_name")
    data["target_product"]=selected.get("asin")
    data["competitor_url"] = selected.get("source_url")
    logger.info("自动发现的竞品：%s", data["competitor"])
    return data

def analysis_task(data):
    logger.info("执行竞品分析任务")
    result=competitor_agent(
        data["target_product"],
        data["competitor"],
    )
    return result
def report_task(result):
    if isinstance(result, dict) and "error" in result:
        logger.warning("报告生成失败，原因：%s", result["error"])
        return result
    logger.info("执行报告生成任务")
    markdown = generate_markdown(
        result
    )
    path=save_report(
        markdown
    )
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