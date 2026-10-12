import logging
import os
from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.tasks import workflow_tasks

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    force=True,
)

if __name__ == '__main__':
    workflow=AnalysisWorkflow()
    for task in workflow_tasks:
        workflow.add_task(task)
    result = workflow.run(
        {
            "target_product": "HuaDisk 256GB nvme ssd amazon"
        }
    )
    print(f"完成，报告已保存到：{result}")