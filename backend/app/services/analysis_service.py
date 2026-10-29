import logging
import os

from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from app.workflow.result import WorkflowResult
from backend.app.queue.task_producer import enqueue_analysis_task
from backend.app.services.task_service import (
    create_task_record,
    save_task_status,
)
from backend.app.services.report_service import (
    save_completed_report,
)
from backend.app.services.result_service import (
    save_analysis_results,
)
from backend.app.services.workflow_service import (
    execute_workflow,
)
load_dotenv()
logger = logging.getLogger(__name__)

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
def create_analysis_task(target_product: str) -> str:
    """创建分析任务，并提交到 Redis 队列。"""

    # 1. 生成唯一任务 ID
    task_id = str(uuid4())

    # 2. MySQL 创建 pending 任务
    create_task_record(
        task_id=task_id,
        target_product=target_product,
    )

    # 3. 提交到 Redis 队列
    try:
        enqueue_analysis_task(
            task_id=task_id,
            target_product=target_product,
        )

        logger.info(
            "分析任务已提交到 Redis，task_id=%s",
            task_id,
        )

    except Exception as exc:
        logger.exception(
            "分析任务入队失败，task_id=%s",
            task_id,
        )

        # Redis 入队失败时，避免 MySQL 一直保持 pending
        try:
            save_task_status(
                task_id=task_id,
                status="failed",
                error=f"Redis 入队失败：{exc}",
            )
        except Exception:
            logger.exception(
                "保存入队失败状态异常，task_id=%s",
                task_id,
            )

        raise

    return task_id



def run_analysis(task_id: str, target_product: str):
    """执行分析任务，任务状态统一保存到 MySQL。"""

    try:
        # 1. 更新任务状态为 running
        save_task_status(
            task_id=task_id,
            status="running",
        )

        # 2. 执行 Mock 或真实 Agent 工作流
        result = execute_workflow(
            task_id=task_id,
            target_product=target_product,
            mock_mode=MOCK_MODE,
        )

        # 3. 检查工作流执行结果
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(str(result["error"]))

        if isinstance(result, WorkflowResult):
            report_path = str(result.report_path)
        elif isinstance(result, (str, Path)):
            report_path = str(result)
        else:
            raise ValueError("工作流未返回有效报告路径")

        if not Path(report_path).is_file():
            raise FileNotFoundError(
                f"报告文件不存在：{report_path}"
            )

        # 4. 商品明细落库：报告是主产物，落库失败不阻断任务完成
        if isinstance(result, WorkflowResult):
            try:
                save_analysis_results(task_id, result)
            except Exception:
                logger.exception(
                    "分析明细落库失败，报告仍会保存，task_id=%s",
                    task_id,
                )

        # 5. 保存报告并更新任务状态为 completed
        save_completed_report(
            task_id=task_id,
            report_path=report_path,
        )

        logger.info(
            "分析任务执行成功，task_id=%s",
            task_id,
        )

    except Exception as exc:
        logger.exception(
            "分析任务执行失败，task_id=%s",
            task_id,
        )

        # 5. 失败状态只保存到 MySQL
        try:
            save_task_status(
                task_id=task_id,
                status="failed",
                error=str(exc),
            )
        except Exception:
            logger.exception(
                "保存 failed 状态失败，task_id=%s",
                task_id,
            )
        raise