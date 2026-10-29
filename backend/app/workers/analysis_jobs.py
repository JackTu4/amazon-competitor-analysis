def execute_analysis_job(task_id: str, target_product: str):
    """RQ 后台竞品分析任务入口。"""

    from backend.app.services.analysis_service import run_analysis

    return run_analysis(
        task_id=task_id,
        target_product=target_product,
    )