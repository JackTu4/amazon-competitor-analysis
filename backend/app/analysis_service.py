import logging
import os
from threading import Thread
from uuid import uuid4

from app.reporter.markdown import save_report
from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.tasks import create_workflow_tasks
logger = logging.getLogger(__name__)
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
analysis_tasks = {}
def run_analysis(task_id: str, target_product: str):
    """在后台启动现有的竞品分析工作流"""
    record=analysis_tasks[task_id]
    record["status"]="running"
    try:
        if MOCK_MODE:
            # 只生成测试报告，不执行真实 Agent
            markdown = f"""# 亚马逊竞品分析报告（模拟）

    ## 目标产品
    - 商品名称：{target_product}

    ## 竞品分析
    - 竞品名称：模拟竞品 A
    - 竞品评分：4.5（模拟数据）

    ## 分析总结
    这是一份用于测试 FastAPI 接口的模拟报告。
    不代表真实商品信息。
    """
            result = save_report(markdown, task_id=task_id)

        else:
            # 正常执行真实 Agent 工作流
            workflow = AnalysisWorkflow()

            for task in create_workflow_tasks():
                workflow.add_task(task)

            result = workflow.run({
                "task_id": task_id,
                "target_product": target_product,
            })
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
    thread = Thread(target=run_analysis, args=(task_id, target_product), daemon=True)  #启动线程  执行相应的后端函数
    thread.start()
    return task_id