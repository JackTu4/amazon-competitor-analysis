from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.task import Task
workflow = AnalysisWorkflow()
workflow.add_task(
    Task(
        name="search"
    )
)
workflow.add_task(
    Task(
        name="read webpage"
    )
)
workflow.add_task(
    Task(
        name="extract product"
    )
)
result=workflow.run()
for task in result:
    print(task)