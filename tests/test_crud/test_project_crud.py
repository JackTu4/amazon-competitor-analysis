import pytest

pytestmark = pytest.mark.integration

from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.db.crud.project import (
    create_project,
    get_project,
    update_project_status,
    list_projects,
    delete_project,
)


def test_project_crud():
    task_id = str(uuid4())

    with SessionLocal() as db:
        try:
            # 1. 创建项目
            create_project(
                db=db,
                task_id=task_id,
                target_product="HUADISK SSD 256GB",
            )

            db.commit()

            # 2. 查询项目
            project = get_project(db, task_id)

            assert project is not None
            assert project.target_product == "HUADISK SSD 256GB"
            assert project.status == "pending"

            print("创建和查询成功")

            # 3. 更新状态
            update_project_status(
                db=db,
                task_id=task_id,
                status="completed",
                result="reports/test.md",
            )

            db.commit()

            project = get_project(db, task_id)

            assert project.status == "completed"
            assert project.result == "reports/test.md"

            print("更新状态成功")

            # 4. 查询历史项目
            projects = list_projects(db)

            assert any(
                item.task_id == task_id
                for item in projects
            )

            print("查询历史项目成功")

            # 5. 删除测试项目
            deleted = delete_project(db, task_id)

            assert deleted is True

            db.commit()

            assert get_project(db, task_id) is None

            print("删除成功")

        finally:
            # 测试失败时也清理本次创建的数据
            db.rollback()

            remaining = get_project(db, task_id)

            if remaining is not None:
                db.delete(remaining)
                db.commit()