import logging

from backend.app.db.database import SessionLocal
from backend.app.db.crud.project import (
    get_project,
    update_project_status,
)
from backend.app.db.crud.project import create_project

logger = logging.getLogger(__name__)


def save_task_status(
    task_id: str,
    status: str,
    result: str | None = None,
    error: str | None = None,
) -> None:
    """更新 MySQL 中的分析任务状态。"""

    with SessionLocal() as db:
        try:
            project = update_project_status(
                db=db,
                task_id=task_id,
                status=status,
                result=result,
                error=error,
            )

            if project is None:
                raise ValueError(
                    f"数据库中不存在任务：{task_id}"
                )

            db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "更新任务状态失败，task_id=%s",
                task_id,
            )
            raise


def get_analysis_task(task_id: str) -> dict | None:
    """根据 task_id 从 MySQL 查询任务。"""

    with SessionLocal() as db:
        project = get_project(
            db=db,
            task_id=task_id,
        )

        if project is None:
            return None

        return {
            "task_id": project.task_id,
            "target_product": project.target_product,
            "status": project.status,
            "result": project.result,
            "error": project.error,
        }
def create_task_record(
    task_id: str,
    target_product: str,
) -> None:
    """在 MySQL 中创建一条分析任务记录。"""

    with SessionLocal() as db:
        try:
            create_project(
                db=db,
                task_id=task_id,
                target_product=target_product,
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "创建数据库任务失败，task_id=%s",
                task_id,
            )
            raise