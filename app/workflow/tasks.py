import logging
from app.agent.agent import competitor_agent
from app.reporter.markdown import (generate_markdown,save_report)
from app.tools.product_review_tool import warmup_product_reviews
from app.workflow.task import Task
from app.agent.competitor_discovery import run_discovery
from app.agent.competitor_verifier import find_target_asin
from concurrent.futures import ThreadPoolExecutor
logger = logging.getLogger(__name__)
def discovery_task(data):
    logger.info("执行自动竞品发现任务")

    target_info = find_target_asin(data["target_product"])

    if not target_info:
        raise ValueError("无法找到目标商品的 ASIN")

    data["target_asin"] = target_info["asin"]

    logger.info("目标商品标题：%s", target_info["title"])
    logger.info("目标商品 ASIN：%s", data["target_asin"])

    # 后台预热目标商品评论，不阻塞竞品发现
    warmup_product_reviews(data["target_asin"])
    logger.info("已在后台提交目标商品评论采集任务")
    result = run_discovery(data["target_product"])

    if hasattr(result, "model_dump"):
        result = result.model_dump()

    logger.info("自动竞品发现完成")

    candidates = result.get("candidates", [])

    if not candidates:
        raise ValueError("自动竞品发现失败：没有找到候选竞品")

    selected = candidates[:3]

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
    """并行分析多个竞品，并保持原始顺序。"""
    logger.info("执行竞品分析任务")

    target = data["target_product"]
    target_asin = data.get("target_asin")
    competitors = data["competitors"]

    logger.info("传入分析流程的目标商品 ASIN：%s", target_asin)
    logger.info("本次需要分析的竞品数量：%s", len(competitors))

    def analyze_one(comp):
        """分析单个竞品，隔离单个竞品的异常。"""
        try:
            result = competitor_agent(
                target,
                comp["name"],
                target_asin=target_asin,
                competitor_asin=comp.get("asin"),
                competitor_url=comp.get("url"),
            )

            return {
                "competitor_name": comp["name"],
                "competitor_asin": comp["asin"],
                "competitor_url": comp["url"],
                "analysis": result,
            }

        except Exception as e:
            logger.exception(
                "竞品分析失败：%s",
                comp.get("name", "未知竞品"),
            )

            return {
                "competitor_name": comp.get("name"),
                "competitor_asin": comp.get("asin"),
                "competitor_url": comp.get("url"),
                "analysis": {
                    "error": str(e),
                },
            }
    # 最多同时分析 3 个竞品
    with ThreadPoolExecutor(max_workers=3) as executor:
        analyses = list(executor.map(analyze_one, competitors))
        successful_analyses = [
            item
            for item in analyses
            if item.get("analysis") is not None
               and not (
                    isinstance(item.get("analysis"), dict)
                    and item["analysis"].get("error")
            )
        ]

        if not successful_analyses:
            raise RuntimeError("所有竞品分析均失败，无法生成有效报告")

    logger.info("竞品分析任务完成，处理数量：%s", len(analyses))

    return {
        "task_id": data.get("task_id"),
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
    path = save_report(
        markdown,
        task_id=result.get("task_id")
    )
    return path

def create_workflow_tasks():     #每次调用都会创建三个新的Task对象  而不只是一个
    return [                     #不同的工作流只能同时修改一个对象，造成任务状态相互覆盖
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
        ),
    ]
