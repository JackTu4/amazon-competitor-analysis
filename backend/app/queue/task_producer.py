from rq.job import Job
from backend.app.queue.rq_config import get_analysis_queue
from backend.app.workers.analysis_jobs import execute_analysis_job
def enqueue_analysis_task(
    task_id: str,
    target_product: str,
) -> Job:
    """将竞品分析任务提交到 Redis 队列。"""
    queue = get_analysis_queue()
    job = queue.enqueue(
        execute_analysis_job,
        task_id,
        target_product,
        job_id=task_id,
        job_timeout=1800,
        result_ttl=3600,
    )
    return job
