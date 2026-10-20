from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock

from app.analyzers.product_review_pipeline import analyze_product_reviews


_review_executor = ThreadPoolExecutor(max_workers=2)
_review_futures: dict[str, Future] = {}
_review_lock = Lock()


def _analyze_reviews(asin: str) -> dict:
    """实际执行评论采集与分析。"""
    result = analyze_product_reviews(asin)
    return result.model_dump()


def warmup_product_reviews(asin: str) -> Future:
    asin = asin.strip().upper()

    with _review_lock:
        future = _review_futures.get(asin)

        # 上次任务已经失败：清掉缓存，允许本次重新提交
        if future is not None and future.done() and future.exception() is not None:
            _review_futures.pop(asin, None)
            future = None

        if future is None:
            future = _review_executor.submit(_analyze_reviews, asin)
            _review_futures[asin] = future

        return future


def analyze_product_reviews_tool(asin: str) -> dict:
    """分析评论，复用同一 ASIN 已提交的任务。"""
    return warmup_product_reviews(asin).result()