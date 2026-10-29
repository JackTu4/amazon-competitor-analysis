from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Project


def create_project(
    db: Session,
    task_id: str,
    target_product: str,
) -> Project:
    """创建分析项目。"""

    project = Project(
        task_id=task_id,
        target_product=target_product,
        status="pending",
    )

    db.add(project)
    db.flush()

    return project


def get_project(
    db: Session,
    task_id: str,
) -> Project | None:
    """根据 task_id 查询分析项目。"""

    return db.get(Project, task_id)


def update_project_status(
    db: Session,
    task_id: str,
    status: str,
    result: str | None = None,
    error: str | None = None,
) -> Project | None:
    """更新任务状态。"""

    project = get_project(db, task_id)

    if project is None:
        return None

    project.status = status
    project.result = result
    project.error = error

    db.flush()

    return project


def list_projects(
    db: Session,
    limit: int = 20,
) -> list[Project]:
    """查询最近创建的分析项目。"""

    stmt = (
        select(Project)
        .order_by(Project.created_at.desc())
        .limit(limit)
    )

    return list(db.scalars(stmt).all())


def delete_project(
    db: Session,
    task_id: str,
) -> bool:
    """删除分析项目。"""

    project = get_project(db, task_id)

    if project is None:
        return False

    db.delete(project)
    db.flush()

    return True