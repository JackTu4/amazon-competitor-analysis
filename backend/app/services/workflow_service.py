import textwrap

from app.reporter.markdown import save_report
from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.result import WorkflowResult
from app.workflow.tasks import create_workflow_tasks


def execute_mock_workflow(
    task_id: str,
    target_product: str,
) -> WorkflowResult:
    """执行模拟分析，生成测试 Markdown 报告。"""

    markdown = textwrap.dedent(
        f"""
        # 亚马逊竞品分析报告（模拟）

        ## 目标商品
        {target_product}

        ## 分析总结
        这是用于测试的模拟报告。
        """
    ).strip()

    path = save_report(
        markdown,
        task_id=task_id,
    )

    return WorkflowResult(
        report_path=path,
        target_product=target_product,
        task_id=task_id,
    )

def execute_agent_workflow(
    task_id: str,
    target_product: str,
):
    """执行真实 Agent 分析工作流。"""
    workflow = AnalysisWorkflow()
    for task in create_workflow_tasks():
        workflow.add_task(task)
    result = workflow.run({
        "task_id": task_id,
        "target_product": target_product,
    })
    return result
def execute_workflow(
    task_id: str,
    target_product: str,
    mock_mode: bool = False,
):
    """根据运行模式选择对应的工作流。"""
    if mock_mode:
        return execute_mock_workflow(
            task_id=task_id,
            target_product=target_product,
        )
    return execute_agent_workflow(
        task_id=task_id,
        target_product=target_product,
    )