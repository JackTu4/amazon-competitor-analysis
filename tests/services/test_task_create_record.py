import pytest

pytestmark = pytest.mark.integration

from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.db.models import Project
from backend.app.services.task_service import create_task_record


def test_create_task_record():
    task_id = str(uuid4())

    try:
        # 1. 调用 Service 创建任务
        create_task_record(
            task_id=task_id,
            target_product="HUADISK SSD 256GB",
        )

        # 2. 使用新 Session 查询数据库
        with SessionLocal() as db:
            project = db.get(Project, task_id)

            assert project is not None
            assert project.task_id == task_id
            assert project.target_product == "HUADISK SSD 256GB"
            assert project.status == "pending"

            print("任务成功写入 MySQL")

    finally:
        # 3. 清理测试数据
        with SessionLocal() as db:
            project = db.get(Project, task_id)

            if project is not None:
                db.delete(project)
                db.commit()