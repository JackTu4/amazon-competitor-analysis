from unittest.mock import patch

from app.workflow.result import WorkflowResult
from backend.app.services.workflow_service import (
    execute_workflow,
)


def test_execute_mock_workflow():
    """Mock 模式应返回带报告路径的 WorkflowResult。"""

    with patch(
        "backend.app.services.workflow_service.save_report",
        return_value="reports/mock.md",
    ) as mock_save:

        result = execute_workflow(
            task_id="test-001",
            target_product="HUADISK SSD",
            mock_mode=True,
        )

        assert isinstance(result, WorkflowResult)
        assert result.report_path == "reports/mock.md"
        assert result.task_id == "test-001"
        assert result.analyses == []

        mock_save.assert_called_once()


def test_execute_agent_workflow():
    """真实 Agent 工作流应把分析结果原样交回。"""

    expected = WorkflowResult(
        report_path="reports/agent.md",
        target_product="HUADISK SSD",
        task_id="test-002",
        analyses=[{"competitor_name": "竞品 A", "analysis": {"error": "timeout"}}],
        failures=[{"competitor_name": "竞品 A", "reason": "timeout"}],
    )

    with (
        patch(
            "backend.app.services.workflow_service.AnalysisWorkflow"
        ) as mock_workflow_class,
        patch(
            "backend.app.services.workflow_service.create_workflow_tasks",
            return_value=["task1", "task2"],
        ),
    ):
        mock_workflow = mock_workflow_class.return_value
        mock_workflow.run.return_value = expected

        result = execute_workflow(
            task_id="test-002",
            target_product="HUADISK SSD",
            mock_mode=False,
        )

        assert result is expected
        assert result.is_degraded

        assert mock_workflow.add_task.call_count == 2

        mock_workflow.run.assert_called_once_with({
            "task_id": "test-002",
            "target_product": "HUADISK SSD",
        })
