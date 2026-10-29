import pytest

pytestmark = pytest.mark.integration

from pathlib import Path
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.db.models import Project, ReportRecord
from backend.app.db.crud.project import create_project
from backend.app.services.report_service import save_completed_report


def test_report_persistence(tmp_path):
    task_id = str(uuid4())

    report_path = tmp_path / f"{task_id}.md"
    markdown = "# 亚马逊竞品分析报告\n\n测试报告内容"
    report_path.write_text(markdown, encoding="utf-8")

    # 1. 创建待分析任务
    with SessionLocal() as db:
        create_project(
            db=db,
            task_id=task_id,
            target_product="HUADISK SSD 256GB",
        )
        db.commit()

    try:
        # 2. 保存报告，并更新任务状态
        save_completed_report(
            task_id=task_id,
            report_path=str(report_path),
        )

        with SessionLocal() as db:
            project = db.get(Project, task_id)

            report = (
                db.query(ReportRecord)
                .filter(ReportRecord.task_id == task_id)
                .first()
            )

            assert project is not None
            assert project.status == "completed"
            assert project.result == str(report_path)

            assert report is not None
            assert report.markdown == markdown
            assert report.file_path == str(report_path)

            print("报告内容保存成功")
            print("任务状态与报告数据一致")

    finally:
        # 先删除报告，再删除项目，避免外键约束错误
        with SessionLocal() as db:
            report = (
                db.query(ReportRecord)
                .filter(ReportRecord.task_id == task_id)
                .first()
            )

            if report is not None:
                db.delete(report)
                db.flush()

            project = db.get(Project, task_id)

            if project is not None:
                db.delete(project)

            db.commit()
