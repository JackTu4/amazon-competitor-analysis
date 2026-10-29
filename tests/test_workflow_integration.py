from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.result import WorkflowResult
from app.workflow.tasks import create_workflow_tasks

from app.models.competitor import (
    CompetitorAnalysis,
    ProductAnalysis,
)

from app.models.extraction import Product


def test_workflow_integration(tmp_path, monkeypatch):
    """
    测试完整工作流：

    竞品发现 -> Agent 分析 -> Markdown 报告生成

    所有外部 API 调用都使用 Mock，
    不会实际调用大模型、Amazon 或 Bright Data。
    """

    # 使用 pytest 临时目录，避免污染真实 reports
    monkeypatch.chdir(tmp_path)

    # 1. 创建模拟任务 ID
    task_id = str(uuid4())

    target_product = "HUADISK 256GB SSD"

    # 2. 模拟目标商品查询结果
    fake_target_info = {
        "title": "HUADISK M.2 NVMe SSD 256GB",
        "asin": "B0TEST0001",
    }

    # 3. 模拟竞品发现结果
    fake_discovery_result = {
        "candidates": [
            {
                "product_name": "模拟竞品 A",
                "asin": "B0TEST0002",
                "source_url": "https://example.com/product-a",
            },
            {
                "product_name": "模拟竞品 B",
                "asin": "B0TEST0003",
                "source_url": "https://example.com/product-b",
            },
        ]
    }

    # 4. 构造模拟的 Agent 分析结果
    def fake_competitor_agent(
        target,
        competitor,
        target_asin=None,
        competitor_asin=None,
        competitor_url=None,
        target_title=None,
        competitor_title=None,
        competitor_brand=None,
    ):
        target_info = ProductAnalysis(
            product=Product(
                name=target,
                title="HUADISK M.2 NVMe SSD 256GB",
                asin=target_asin,
                brand="HUADISK",
            ),
            bullet_points=[
                "256GB 存储容量",
                "支持 NVMe 接口",
            ],
            rating=4.5,
            reviews=100,
            price=None,
        )

        competitor_info = ProductAnalysis(
            product=Product(
                name=competitor,
                title=f"{competitor} 256GB SSD",
                asin=competitor_asin,
                brand="TestBrand",
            ),
            bullet_points=[
                "256GB 存储容量",
                "支持 NVMe 接口",
            ],
            rating=4.3,
            reviews=80,
            price=None,
        )

        return CompetitorAnalysis(
            target_product=target_info,
            competitor=competitor_info,
            price_difference=None,
            summary="模拟分析：两款产品容量相同，评分略有差异。",
        )

    # 5. 替换所有可能产生真实费用的外部调用
    with (
        patch(
            "app.workflow.tasks.find_target_asin",
            return_value=fake_target_info,
        ) as mock_target,

        patch(
            "app.workflow.tasks.warmup_product_reviews"
        ) as mock_reviews,

        patch(
            "app.workflow.tasks.run_discovery",
            return_value=fake_discovery_result,
        ) as mock_discovery,

        patch(
            "app.workflow.tasks.competitor_agent",
            side_effect=fake_competitor_agent,
        ) as mock_agent,
    ):

        # 6. 创建真实工作流
        workflow = AnalysisWorkflow()

        for task in create_workflow_tasks():
            workflow.add_task(task)

        # 7. 执行工作流
        result = workflow.run({
            "task_id": task_id,
            "target_product": target_product,
        })

        # 8. 验证外部调用确实被 Mock
        mock_target.assert_called_once_with(target_product)
        mock_reviews.assert_called_once_with("B0TEST0001")
        mock_discovery.assert_called_once_with(target_product)

        # 两个模拟竞品应该调用两次 Agent
        assert mock_agent.call_count == 2

    # 9. 验证工作流返回结构化结果
    assert isinstance(result, WorkflowResult), (
        f"工作流没有返回 WorkflowResult：{type(result)}"
    )

    assert len(result.analyses) == 2
    assert result.failures == []
    assert result.target_asin == "B0TEST0001"

    report_path = Path(result.report_path)

    # 10. 验证报告文件存在
    assert report_path.is_file(), (
        f"报告文件不存在：{report_path}"
    )

    # 11. 验证文件名包含 task_id
    assert report_path.name == f"{task_id}.md"

    # 12. 读取 Markdown 报告
    markdown = report_path.read_text(encoding="utf-8")

    # 13. 验证报告内容
    assert "# 亚马逊竞品分析报告" in markdown
    assert "HUADISK 256GB SSD" in markdown
    assert "模拟竞品 A" in markdown
    assert "模拟竞品 B" in markdown
    assert "核心指标对比" in markdown
    assert "模拟分析" in markdown

    # 14. 验证三个工作流任务的执行状态
    assert len(workflow.tasks) == 3

    for task in workflow.tasks:
        assert task.status == "done", (
            f"任务 {task.name} 执行失败：{task.error}"
        )

    print("\n========== 工作流测试成功 ==========")
    print("任务 ID：", task_id)
    print("报告路径：", report_path)
    print("报告大小：", len(markdown), "字符")
    print("Agent 模拟调用次数：", mock_agent.call_count)
    print("===================================")