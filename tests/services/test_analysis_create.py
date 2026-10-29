"""创建分析任务的单元测试：不依赖 MySQL / Redis，全部打桩。"""

from unittest.mock import patch

import pytest

from backend.app.services import analysis_service


def test_create_analysis_task_enqueues():
    """任务应先写 MySQL 记录，再投递到 Redis 队列。"""

    with (
        patch.object(
            analysis_service, "create_task_record"
        ) as create_record,
        patch.object(
            analysis_service, "enqueue_analysis_task"
        ) as enqueue,
    ):
        task_id = analysis_service.create_analysis_task(
            "HUADISK SSD 256GB"
        )

    # task_id 是 UUID4 字符串
    assert isinstance(task_id, str)
    assert len(task_id) == 36

    create_record.assert_called_once_with(
        task_id=task_id,
        target_product="HUADISK SSD 256GB",
    )
    enqueue.assert_called_once_with(
        task_id=task_id,
        target_product="HUADISK SSD 256GB",
    )


def test_enqueue_failure_marks_task_failed():
    """入队失败时，应把任务标记为 failed 并把异常继续抛出。"""

    with (
        patch.object(analysis_service, "create_task_record"),
        patch.object(
            analysis_service,
            "enqueue_analysis_task",
            side_effect=RuntimeError("redis down"),
        ),
        patch.object(
            analysis_service, "save_task_status"
        ) as save_status,
    ):
        with pytest.raises(RuntimeError, match="redis down"):
            analysis_service.create_analysis_task("HUADISK SSD")

    save_status.assert_called_once()

    kwargs = save_status.call_args.kwargs

    assert kwargs["status"] == "failed"
    assert "redis down" in kwargs["error"]
