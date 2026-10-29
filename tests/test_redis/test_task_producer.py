import pytest

pytestmark = pytest.mark.integration

from uuid import uuid4

from backend.app.queue.task_producer import enqueue_analysis_task


def test_enqueue_analysis_task():
    task_id = str(uuid4())
    target_product = "HUADISK 256GB SSD"

    job = enqueue_analysis_task(
        task_id=task_id,
        target_product=target_product,
    )

    assert job.id == task_id

    assert job.func_name == (
        "backend.app.workers.analysis_jobs.execute_analysis_job"
    )

    assert job.args == (task_id, target_product)

    print("任务提交成功")
    print("Task ID:", task_id)
    print("RQ Job ID:", job.id)
    print("任务状态:", job.get_status(refresh=True))
