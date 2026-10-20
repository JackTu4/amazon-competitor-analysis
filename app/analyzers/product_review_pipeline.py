import threading
import logging
from app.tools.brightdata_reviews import collect_amazon_reviews
from app.analyzers.user_analyzer import analyze_review_sentiment
from app.models.review_analysis import ReviewAnalysis
logger = logging.getLogger(__name__)
# ---- single-flight 缓存：同一 ASIN 并发只执行一次 ----
# entry 结构: {"done": Event, "result": ReviewAnalysis, "error": Exception|None}
_review_cache: dict[str, dict] = {}
_review_cache_lock = threading.Lock()

def analyze_product_reviews(asin: str) -> ReviewAnalysis:
    """自动采集Amazon评论分析用户反馈（同一 ASIN 并发只执行一次，其余等待复用结果）"""

    # 快速路径：拿锁看缓存里有没有正在跑/已跑完的 entry
    with _review_cache_lock:
        if asin in _review_cache:
            entry = _review_cache[asin]
            leader = False
        else:
            entry = {"done": threading.Event(), "result": None, "error": None}
            _review_cache[asin] = entry
            leader = True

    # 不是 leader → 等 leader 跑完，直接复用结果
    if not leader:
        entry["done"].wait()
        if entry["error"] is not None:
            raise entry["error"]
        return entry["result"]

    # leader：真正执行采集 + 分析
    try:
        logger.info(
            "开始采集评论, asin=%s, thread=%s",
            asin,
            threading.current_thread().name,
        )
        # 第一步:自动采集评论
        reviews = collect_amazon_reviews(
            asin=asin,
            max_reviews=3,
        )
        # 第二步：分析评论
        result = analyze_review_sentiment(reviews)
        entry["result"] = result
        return result
    except Exception as e:
        entry["error"] = e
        raise
    finally:
        entry["done"].set()
        # 失败的 entry 从缓存里删掉，让下次调用重新当 leader
        if entry["error"] is not None:
            with _review_cache_lock:
                _review_cache.pop(asin, None)
