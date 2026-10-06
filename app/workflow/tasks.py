from app.agent.agent import competitor_agent
from app.reporter.markdown import (generate_markdown,save_report)
from app.workflow.task import Task
def analysis_task(data):
    print("执行竞品分析任务")
    result=competitor_agent(
        data["target_product"],
        data["competitor"],
    )
    return result
def report_task(result):
    print("执行报告生成任务")
    markdown = generate_markdown(
        result
    )
    path=save_report(
        markdown
    )
    return path
workflow_tasks=[
    Task(
        name="competitor_analysis",
        func=analysis_task,
    ),
    Task(
        name="generate_report",
        func=report_task,
    )
]