import logging
from threading import Thread
from uuid import uuid4
from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.tasks import workflow_tasks
logger = logging.getLogger(__name__)
analysis_tasks = {}
def run_analysis(task_id: str, target_product: str):
    """在后台启动现有的竞品分析工作流"""
    record=analysis_tasks[task_id]
    record["status"]="running"
    try:
        workflow=AnalysisWorkflow()
        for task in workflow_tasks:
            workflow.add_task(task)
        result=workflow.run({
            "target_product":target_product}
        )
        if isinstance(result,dict) and "error" in result:
            record["status"]="failed"
            record["error"]=result["error"]
        else:
            record["status"]="completed"
            record["result"]=result
    except Exception as exc:
        logger.exception("分析任务执行失败，task_id=%s", task_id)
        record["status"] = "failed"
        record["error"] = str(exc)
def create_analysis_task(target_product: str) -> str:
    """创建任务并启动后台线程。"""
    task_id = str(uuid4())
    analysis_tasks[task_id] = {
        "task_id": task_id,
        "target_product": target_product,
        "status": "pending",
        "result": None,
        "error": None
    }
    thread = Thread(target=run_analysis, args=(task_id, target_product), daemon=True)
    thread.start()
    return task_id