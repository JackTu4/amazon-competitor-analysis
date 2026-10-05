from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.task import Task
from app.workflow.tasks import (
    search_task,
    read_task,
    extract_task
)
workflow = AnalysisWorkflow()
workflow.add_task(Task(    # Task将普通函数包装成任务
    name="search",
    func=lambda:
    search_task(
        "Huadisk SSD Amazon"
    )
))
workflow.add_task(
    Task(
        name="read",
        func=read_task
    )
)
workflow.add_task(
    Task(
        name="extract",
        func=lambda data:
        extract_task(data)
    )
)
results=workflow.run()
for task in results:
    print("=============")
    print(task.name)
    print(task.status)
    print(task.result)
    print("错误:")
    print(task.error)