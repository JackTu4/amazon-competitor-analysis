from rq import Worker

from backend.app.queue.redis_client import get_redis_connection


def start_worker():
    """启动 Linux RQ Worker。"""

    redis_conn = get_redis_connection()

    worker = Worker(
        queues=["analysis"],
        connection=redis_conn,
    )

    print("Linux RQ Worker 正在监听 analysis 队列")

    worker.work()


if __name__ == "__main__":
    start_worker()
