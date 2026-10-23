import logging
import os
from threading import Thread
from uuid import uuid4
import textwrap
from app.reporter.markdown import save_report
from app.workflow.analysis_workflow import AnalysisWorkflow
from app.workflow.tasks import create_workflow_tasks
from pathlib import Path
logger = logging.getLogger(__name__)
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
analysis_tasks = {}
def run_analysis(task_id: str, target_product: str):
    """在后台启动现有的竞品分析工作流"""
    record=analysis_tasks[task_id]
    record["status"]="running"
    try:

        if MOCK_MODE:
            markdown = textwrap.dedent(f"""
        # 亚马逊竞品分析报告（模拟）

        ## 目标产品
        - 商品名称：{target_product}

        ## 竞品分析
        - 竞品名称：模拟竞品 A
        - 竞品评分：4.5（模拟数据）

        ## 分析总结
        这是一份用于测试 FastAPI 接口的模拟报告。
        不代表真实商品信息。
        """).strip()
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
        if isinstance(result, dict) and "error" in result:
            record["status"] = "failed"
            record["error"] = result["error"]

        elif not isinstance(result, (str, Path)):
            record["status"] = "failed"
            record["error"] = "工作流未返回有效报告路径"

        elif not Path(result).is_file():
            record["status"] = "failed"
            record["error"] = f"报告文件不存在：{result}"

        else:
            record["result"] = str(result)
            record["status"] = "completed"

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