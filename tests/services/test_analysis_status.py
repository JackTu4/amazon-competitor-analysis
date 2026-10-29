"""任务状态落库的集成测试：需要本地 MySQL 与 .env 配置。"""

from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from backend.app.db.database import SessionLocal
from backend.app.db.models import Project, ReportRecord
from backend.app.services import analysis_service
from backend.app.services.task_service import create_task_record

pytestmark = pytest.mark.integration


def test_run_analysis_completes_task(tmp_path, monkeypatch):
    """Mock 模式下执行分析，任务应变为 completed 并写入报告。"""

    # 报告文件写到临时目录，避免污染项目 reports/
    monkeypatch.chdir(tmp_path)

    task_id = str(uuid4())
    target_product = "HUADISK SSD 256GB"

    create_task_record(
        task_id=task_id,
        target_product=target_product,
    )

    try:
        # 强制走 Mock 工作流，不调用任何外部 API
        with patch.object(analysis_service, "MOCK_MODE", True):
            analysis_service.run_analysis(task_id, target_product)

        with SessionLocal() as db:
            project = db.get(Project, task_id)

            assert project is not None
            assert project.status == "completed"
            assert project.error is None
            assert project.result is not None

            report_path = Path(project.result)
            assert report_path.is_file(), f"报告文件不存在：{report_path}"

            report = (
                db.query(ReportRecord)
                .filter(ReportRecord.task_id == task_id)
                .first()
            )

            assert report is not None
            assert "模拟" in report.markdown
            assert report.file_path == project.result

    finally:
        # 先删报告，再删任务，避免外键约束报错
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
