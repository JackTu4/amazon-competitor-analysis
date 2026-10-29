import pytest

pytestmark = pytest.mark.integration

from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.db.crud.project import create_project
from backend.app.db.crud.report import (
    create_report,
    get_report,
    update_report,
    delete_report,
)


def test_report_crud():
    task_id = str(uuid4())

    with SessionLocal() as db:
        try:
            # 1. 创建分析项目
            create_project(
                db=db,
                task_id=task_id,
                target_product="HUADISK SSD 256GB",
            )

            # 2. 创建 Markdown 报告
            markdown = """
# 亚马逊竞品分析报告

## 目标商品
HUADISK SSD 256GB

## 分析总结
测试报告内容。
"""

            create_report(
                db=db,
                task_id=task_id,
                markdown=markdown,
                file_path=f"reports/{task_id}.md",
            )

            # 3. 查询报告
            report = get_report(db, task_id)

            assert report is not None
            assert report.task_id == task_id
            assert "HUADISK" in report.markdown

            print("创建和查询报告成功")

            # 4. 更新报告
            new_markdown = """
# 亚马逊竞品分析报告

## 分析总结
更新后的测试报告。
"""

            update_report(
                db=db,
                task_id=task_id,
                markdown=new_markdown,
            )

            updated = get_report(db, task_id)

            assert "更新后的测试报告" in updated.markdown

            print("更新报告成功")

            # 5. 删除报告
            deleted = delete_report(db, task_id)

            assert deleted is True
            assert get_report(db, task_id) is None

            print("删除报告成功")

        finally:
            # 测试结束后回滚
            db.rollback()
