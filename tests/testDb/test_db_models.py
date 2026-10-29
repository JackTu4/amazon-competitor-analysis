import pytest

pytestmark = pytest.mark.integration

from sqlalchemy import inspect

from backend.app.db.database import Base, engine
from backend.app.db.models import Project


def test_create_projects_table():
    # 根据 ORM 模型创建不存在的表
    Base.metadata.create_all(bind=engine)

    # 检查数据库中的表
    inspector = inspect(engine)

    assert inspector.has_table("projects")

    # 检查字段
    columns = inspector.get_columns("projects")
    column_names = {column["name"] for column in columns}

    expected = {
        "task_id",
        "target_product",
        "status",
        "result",
        "error",
        "created_at",
        "updated_at",
    }

    assert expected.issubset(column_names)

    print("projects 表创建成功")
    print("字段：", sorted(column_names))
def test_create_all_tables():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "projects",
        "products",
        "sources",
        "reports",
    }

    assert expected_tables.issubset(tables)

    print("数据库表创建成功：", sorted(expected_tables))
