import logging
from app.agent.agent import competitor_agent
from app.reporter.markdown import (generate_markdown,save_report)
from app.tools.product_review_tool import warmup_product_reviews
from app.workflow.task import Task
from app.agent.competitor_discovery import run_discovery
from app.agent.competitor_verifier import find_target_asin
from app.workflow.result import WorkflowResult
from concurrent.futures import ThreadPoolExecutor
logger = logging.getLogger(__name__)


def collect_failures(analyses):
    """从分析结果里挑出失败或被跳过的竞品。"""

    failures = []

    for item in analyses or []:
        analysis = item.get("analysis")

        if isinstance(analysis, dict) and analysis.get("error"):
            failures.append({
                "competitor_name": item.get("competitor_name") or "未知竞品",
                "competitor_asin": item.get("competitor_asin"),
                "reason": (
                    analysis.get("message")
                    or analysis.get("error")
                ),
            })
            continue

        if analysis is None:
            failures.append({
                "competitor_name": item.get("competitor_name") or "未知竞品",
                "competitor_asin": item.get("competitor_asin"),
                "reason": item.get("error") or "分析结果为空",
            })

    return failures

def discovery_task(data):
    logger.info("执行自动竞品发现任务")

    target_info = find_target_asin(data["target_product"])

    if not target_info:
        raise ValueError("无法找到目标商品的 ASIN")

    data["target_asin"] = target_info["asin"]
    # 已核验的标题要传下去，避免分析阶段重复抓 Amazon 时被反爬拦截
    data["target_title"] = target_info.get("title") or ""

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
            # 搜索结果里的原始标题，详情页被降级时用它兜底
            "title": c.get("source_title") or c.get("product_name"),
            "brand": c.get("brand"),
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
    target_title = data.get("target_title")
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
                target_title=target_title,
                competitor_title=comp.get("title"),
                competitor_brand=comp.get("brand"),
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
        "target_asin": target_asin,
        "analyses": analyses,
    }

def report_task(result):
    if isinstance(result, dict) and "error" in result:
        logger.warning("报告生成失败，原因：%s", result["error"])
        return result

    analyses = result.get("analyses", [])
    failures = collect_failures(analyses)

    logger.info(
        "交给报告生成器的竞品分析数量：%s，失败数量：%s",
        len(analyses),
        len(failures),
    )
    logger.info("执行报告生成任务")

    markdown = generate_markdown(result)
    path = save_report(
        markdown,
        task_id=result.get("task_id")
    )

    # 把结构化结果一并交回，供 backend 落库
    return WorkflowResult(
        report_path=path,
        target_product=result.get("target_product") or "",
        task_id=result.get("task_id"),
        target_asin=result.get("target_asin"),
        analyses=analyses,
        failures=failures,
    )

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
