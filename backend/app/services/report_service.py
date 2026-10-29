import logging
from pathlib import Path

from backend.app.db.database import SessionLocal
from backend.app.db.crud.report import (
    create_report,
    get_report,
)
from backend.app.db.crud.project import update_project_status

logger = logging.getLogger(__name__)


def save_completed_report(task_id: str, report_path: str) -> None:
    """保存 Markdown 报告，并同步更新任务完成状态。"""

    path = Path(report_path)

    # 1. 检查报告文件
    if not path.is_file():
        raise FileNotFoundError(
            f"报告文件不存在：{report_path}"
        )

    markdown = path.read_text(encoding="utf-8")

    if not markdown.strip():
        raise ValueError("报告内容不能为空")

    # 2. 开启数据库事务
    with SessionLocal() as db:
        try:
            report = get_report(db, task_id)

            # 3. 保存或更新报告
            if report is None:
                create_report(
                    db=db,
                    task_id=task_id,
                    markdown=markdown,
                    file_path=report_path,
                )
            else:
                report.markdown = markdown
                report.file_path = report_path

            # 4. 更新任务状态
            project = update_project_status(
                db=db,
                task_id=task_id,
                status="completed",
                result=report_path,
                error=None,
            )

            if project is None:
                raise ValueError(
                    f"任务不存在：{task_id}"
                )

            # 5. 同一个事务提交
            db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "保存分析报告失败，task_id=%s",
                task_id,
            )

            raise


def get_analysis_report(task_id: str) -> dict | None:
    """根据 task_id 从 MySQL 查询分析报告。"""

    with SessionLocal() as db:
        report = get_report(db, task_id)

        if report is None:
            return None

        return {
            "task_id": report.task_id,
            "report": report.markdown,
            "file_path": report.file_path,
        }
