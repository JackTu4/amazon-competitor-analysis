from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.tasks import workflow_tasks
if __name__ == '__main__':
    workflow=AnalysisWorkflow()
    for task in workflow_tasks:
        workflow.add_task(task)
    result=workflow.run(
        {
            "target_product":"Huadisk nvme ssd amazon",
            "competitor":"Sumsam nvme ssd amazon"
        }
    )
    print("完成")
    print(result)