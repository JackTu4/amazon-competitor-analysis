from app.workflow.task import Task
task=Task(
    name="search_product"
)
print(task)
task.status="running"
print(task)
task.status="done"
task.result="搜索完成"
print(task)