from sqlalchemy.orm import Session

from backend.app.db.models import ReportRecord


def create_report(
    db: Session,
    task_id: str,
    markdown: str,
    file_path: str | None = None,
) -> ReportRecord:
    """创建分析报告。"""

    if not markdown.strip():
        raise ValueError("markdown 内容不能为空")

    report = ReportRecord(
        task_id=task_id,
        markdown=markdown,
        file_path=file_path,
    )

    db.add(report)
    db.flush()

    return report


def get_report(
    db: Session,
    task_id: str,
) -> ReportRecord | None:
    """根据 task_id 查询报告。"""

    return (
        db.query(ReportRecord)
        .filter(ReportRecord.task_id == task_id)
        .first()
    )


def update_report(
    db: Session,
    task_id: str,
    markdown: str | None = None,
    file_path: str | None = None,
) -> ReportRecord | None:
    """更新报告内容或文件路径。"""

    report = get_report(db, task_id)

    if report is None:
        return None

    if markdown is not None:
        if not markdown.strip():
            raise ValueError("markdown 内容不能为空")

        report.markdown = markdown

    if file_path is not None:
        report.file_path = file_path

    db.flush()

    return report


def delete_report(
    db: Session,
    task_id: str,
) -> bool:
    """根据 task_id 删除报告。"""

    report = get_report(db, task_id)

    if report is None:
        return False

    db.delete(report)
    db.flush()

    return True