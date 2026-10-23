import time
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import analysis_service


def test_analysis_api(tmp_path, monkeypatch):
    """
    测试 FastAPI 完整接口流程：
    创建任务 -> 查询状态 -> 获取报告。

    模拟工作流执行，不调用任何真实外部 API。
    """

    # 将报告写入 pytest 临时目录
    monkeypatch.chdir(tmp_path)

    # 确保使用独立的测试任务记录
    analysis_service.analysis_tasks.clear()

    # 这次测试要进入真实工作流分支，
    # 但工作流本身使用 Mock，不会调用外部 API
    monkeypatch.setattr(
        analysis_service,
        "MOCK_MODE",
        False
    )

    def fake_workflow_run(self, input_data):
        task_id = input_data["task_id"]

        report_path = Path("reports") / f"{task_id}.md"
        report_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        report_path.write_text(
            "# 模拟竞品分析报告\n\n"
            "## 目标产品\n"
            "- 商品名称：HUADISK 256GB SSD\n\n"
            "## 分析总结\n"
            "FastAPI 工作流集成测试成功。\n",
            encoding="utf-8"
        )

        return report_path

    # 仅替换工作流执行方法
    with patch.object(
        analysis_service.AnalysisWorkflow,
        "run",
        fake_workflow_run
    ):
        with TestClient(app) as client:

            # 1. 创建分析任务
            response = client.post(
                "/api/analysis",
                json={
                    "target_product": "HUADISK 256GB SSD"
                }
            )

            assert response.status_code == 200

            data = response.json()
            task_id = data["task_id"]

            assert task_id

            # 2. 查询任务状态
            # 最多轮询 30 次，避免无限等待
            status_data = None

            for _ in range(30):
                status_response = client.get(
                    f"/api/analysis/{task_id}"
                )

                assert status_response.status_code == 200

                status_data = status_response.json()

                if status_data["status"] in (
                    "completed",
                    "failed"
                ):
                    break

                time.sleep(0.1)

            assert status_data["status"] == "completed", (
                f"任务没有成功完成：{status_data}"
            )

            # 3. 获取分析报告
            report_response = client.get(
                f"/api/analysis/{task_id}/report"
            )

            assert report_response.status_code == 200

            report_data = report_response.json()

            assert report_data["status"] == "completed"
            assert "模拟竞品分析报告" in report_data["report"]
            assert "HUADISK 256GB SSD" in report_data["report"]

            print("\n========== FastAPI 集成测试通过 ==========")
            print("任务 ID：", task_id)
            print("任务状态：", status_data["status"])
            print("报告字符数：", len(report_data["report"]))
            print("========================================")
