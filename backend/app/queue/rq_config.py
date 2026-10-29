from rq import Queue

from backend.app.queue.redis_client import get_redis_connection


def get_analysis_queue() -> Queue:
    """获取竞品分析任务队列。"""

    return Queue(
        name="analysis",
        connection=get_redis_connection(),
        default_timeout=1800,
    )