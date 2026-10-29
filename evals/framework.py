"""评估框架公共能力：配置、用量统计、评分、落盘。"""
from __future__ import annotations
import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

# framework.py 在项目根目录
FRAMEWORK_PATH = Path(__file__).resolve()   # E:\Analysis System\evals\framework.py
EVALS_DIR = FRAMEWORK_PATH.parent           # E:\Analysis System\evals
PROJECT_ROOT = EVALS_DIR.parent             # E:\Analysis System 真正项目根目录

CASES_PATH = EVALS_DIR / "cases.json"
PRICING_PATH = EVALS_DIR / "pricing.json"

# 让 `python -m evals.xxx` 之外的方式也能 import 到 app / backend
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_DIR = EVALS_DIR / "results"
LOGS_DIR = EVALS_DIR / "logs"

PRODUCT_FIELDS = (
    "name",
    "title",
    "asin",
    "brand",
    "price",
    "currency",
    "rating",
    "reviews",
)
SCORED_COMPETITORS = 3

PRICE_TOLERANCE = 0.05
RATING_TOLERANCE = 0.1
REVIEWS_TOLERANCE = 0.10
REVIEWS_FLOOR = 50

logger = logging.getLogger("evals")


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_cases() -> list[dict]:
    cases = load_json(CASES_PATH)

    if not isinstance(cases, list) or not cases:
        raise ValueError("cases.json 必须是非空数组")

    ids = [case.get("id") for case in cases]

    if any(not case_id for case_id in ids):
        raise ValueError("每个案例都必须有 id")

    if len(ids) != len(set(ids)):
        raise ValueError("cases.json 存在重复 id")

    return cases


def load_pricing() -> dict:
    return load_json(PRICING_PATH)


def write_json(path: Path, data: Any) -> None:
    """先写临时文件再替换，避免中途退出留下半个 JSON。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())

    temp_path.replace(path)


def setup_logging(case_id: str) -> Path:
    ensure_dirs()
    log_path = LOGS_DIR / f"{case_id}.log"

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)

    return log_path


def git_state() -> dict:
    def run(args: list[str]) -> str:
        try:
            completed = subprocess.run(
                args,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return completed.stdout.strip()
        except Exception:
            return ""

    changed = [
        line
        for line in run(["git", "status", "--short"]).splitlines()
        if line.strip()
    ]

    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "dirty": bool(changed),
        "changed_files": len(changed),
    }


class UsageTracker:
    """统计 LLM token 与外部工具调用次数。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._installed = False
        self.data = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "embedding_tokens": 0,
            "llm_calls": 0,
            "embedding_calls": 0,
            "usage_missing": 0,
            "tavily_calls": 0,
            "brightdata_jobs": 0,
        }

    def add(self, key: str, value: int = 1) -> None:
        with self._lock:
            self.data[key] += value

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self.data)

    def install(self) -> None:
        """给 OpenAI SDK 和外部工具打补丁，只影响当前进程。"""

        if self._installed:
            return

        from openai.resources.chat.completions import Completions
        from openai.resources.embeddings import Embeddings

        tracker = self

        original_chat = Completions.create

        def chat_create(self, *args, **kwargs):
            response = original_chat(self, *args, **kwargs)
            usage = getattr(response, "usage", None)

            with tracker._lock:
                tracker.data["llm_calls"] += 1
                if usage is None:
                    tracker.data["usage_missing"] += 1
                else:
                    tracker.data["prompt_tokens"] += (
                        getattr(usage, "prompt_tokens", 0) or 0
                    )
                    tracker.data["completion_tokens"] += (
                        getattr(usage, "completion_tokens", 0) or 0
                    )

            return response

        Completions.create = chat_create

        original_embed = Embeddings.create

        def embed_create(self, *args, **kwargs):
            response = original_embed(self, *args, **kwargs)
            usage = getattr(response, "usage", None)

            with tracker._lock:
                tracker.data["embedding_calls"] += 1

                if usage is None:
                    tracker.data["usage_missing"] += 1
                    total = 0
                else:
                    total = getattr(usage, "total_tokens", None)

                    if total is None:
                        total = (
                            getattr(usage, "prompt_tokens", 0) or 0
                        ) + (
                            getattr(usage, "completion_tokens", 0) or 0
                        )

                tracker.data["embedding_tokens"] += total or 0

            return response

        Embeddings.create = embed_create

        try:
            import app.tools.web_search as web_search

            original_search = web_search.tavily_client.search

            def counted_search(*args, **kwargs):
                tracker.add("tavily_calls")
                return original_search(*args, **kwargs)

            web_search.tavily_client.search = counted_search
        except Exception:
            logger.exception("Tavily 计数补丁安装失败")

        try:
            import app.analyzers.product_review_pipeline as review_pipeline

            original_reviews = review_pipeline.collect_amazon_reviews

            def counted_reviews(*args, **kwargs):
                tracker.add("brightdata_jobs")
                return original_reviews(*args, **kwargs)

            review_pipeline.collect_amazon_reviews = counted_reviews
        except Exception:
            logger.exception("BrightData 计数补丁安装失败")

        self._installed = True


def normalize(value: Any) -> str:
    return str(value or "").strip().casefold()


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    return int(number) if number is not None else None


def target_field_checks(
    expected: dict,
    target: dict | None,
) -> dict[str, bool | None]:
    """逐字段比对目标商品。返回 None 表示该字段没有预期值，不参与计分。"""

    checks: dict[str, bool | None] = {}

    expected_asin = normalize(expected.get("target_asin"))
    actual_asin = normalize((target or {}).get("asin"))

    if not expected_asin:
        checks["asin"] = None
    else:
        checks["asin"] = actual_asin == expected_asin

    expected_brand = normalize(expected.get("brand"))
    actual_brand = normalize((target or {}).get("brand"))

    if not expected_brand:
        checks["brand"] = None
    else:
        checks["brand"] = bool(actual_brand) and (
            expected_brand in actual_brand or actual_brand in expected_brand
        )

    expected_price = as_float(expected.get("price"))
    actual_price = as_float((target or {}).get("price"))

    if expected_price is None:
        checks["price"] = None
    else:
        checks["price"] = (
            actual_price is not None
            and abs(actual_price - expected_price)
            / max(abs(expected_price), 0.01)
            <= PRICE_TOLERANCE
        )

    expected_rating = as_float(expected.get("rating"))
    actual_rating = as_float((target or {}).get("rating"))

    if expected_rating is None:
        checks["rating"] = None
    else:
        checks["rating"] = (
            actual_rating is not None
            and abs(actual_rating - expected_rating) <= RATING_TOLERANCE
        )

    expected_reviews = as_int(expected.get("reviews"))
    actual_reviews = as_int((target or {}).get("reviews"))

    if expected_reviews is None:
        checks["reviews"] = None
    else:
        checks["reviews"] = (
            actual_reviews is not None
            and abs(actual_reviews - expected_reviews)
            <= max(REVIEWS_FLOOR, abs(expected_reviews) * REVIEWS_TOLERANCE)
        )

    return checks


def rate_checks(checks: dict[str, bool | None]) -> float | None:
    scored = [value for value in checks.values() if value is not None]

    if not scored:
        return None

    return sum(1 for value in scored if value) / len(scored)


def competitor_checks(
    competitor: dict,
    target: dict | None,
    expected: dict,
) -> dict[str, bool | None]:
    text = f'{competitor.get("title") or ""} {competitor.get("name") or ""}'.lower()
    keywords = [
        str(keyword).lower()
        for keyword in expected.get("category_keywords", [])
        if keyword
    ]

    target_asin = normalize((target or {}).get("asin"))
    target_brand = normalize((target or {}).get("brand"))
    competitor_brand = normalize(competitor.get("brand"))

    # 品牌写法常带后缀（Samsung / Samsung Electronics），用包含关系判断同一品牌
    same_brand = (
        bool(target_brand)
        and bool(competitor_brand)
        and (
            competitor_brand in target_brand
            or target_brand in competitor_brand
        )
    )

    checks: dict[str, bool | None] = {
        "asin_format": (
            bool(competitor.get("asin"))
            and len(str(competitor["asin"]).strip()) == 10
        ),
        "not_target": (
            bool(competitor.get("asin"))
            and normalize(competitor.get("asin")) != target_asin
        ),
        "different_brand": (
            None
            if not target_brand
            else bool(competitor_brand) and not same_brand
        ),
        "category": (
            any(keyword in text for keyword in keywords) if keywords else None
        ),
        "fields_present": all(
            competitor.get(field) is not None
            for field in ("price", "rating", "reviews")
        ),
        "source_present": bool(competitor.get("sources")),
    }

    return checks


def competitor_is_valid(checks: dict[str, bool | None]) -> bool:
    for field in ("asin_format", "not_target", "different_brand", "category"):
        if checks[field] is False:
            return False

    return bool(checks["asin_format"])


def score_competitors(
    competitors: list[dict],
    target: dict | None,
    expected: dict,
) -> dict:
    scored = competitors[:SCORED_COMPETITORS]

    if not scored:
        return {"rate": 0.0, "valid_count": 0, "details": []}

    details = []
    rates = []
    valid_count = 0

    for competitor in scored:
        checks = competitor_checks(competitor, target, expected)
        rate = rate_checks(checks)
        details.append({
            "asin": competitor.get("asin"),
            "name": competitor.get("name"),
            "checks": checks,
            "rate": rate,
        })

        if rate is not None:
            rates.append(rate)

        valid_count += int(competitor_is_valid(checks))

    return {
        "rate": sum(rates) / len(rates) if rates else 0.0,
        "valid_count": valid_count,
        "details": details,
    }


def completeness(products: list[dict]) -> float:
    if not products:
        return 0.0

    filled = sum(
        1
        for product in products
        for field in PRODUCT_FIELDS
        if product.get(field) not in (None, "")
    )

    return filled / (len(products) * len(PRODUCT_FIELDS))


def report_sections(markdown: str) -> list[str]:
    return [
        line.lstrip("#").strip()
        for line in markdown.splitlines()
        if line.startswith("#") and line.lstrip("#").strip()
    ]


def compute_cost(usage: dict, pricing: dict) -> dict:
    llm = (
        usage.get("prompt_tokens", 0)
        / 1_000_000
        * float(pricing.get("llm_input_per_1m", 0))
    ) + (
        usage.get("completion_tokens", 0)
        / 1_000_000
        * float(pricing.get("llm_output_per_1m", 0))
    )

    embedding = (
        usage.get("embedding_tokens", 0)
        / 1_000_000
        * float(pricing.get("embedding_per_1m", 0))
    )

    external = (
        usage.get("tavily_calls", 0)
        * float(pricing.get("tavily_per_search", 0))
    ) + (
        usage.get("brightdata_jobs", 0)
        * float(pricing.get("brightdata_per_job", 0))
    )

    return {
        "llm": round(llm, 6),
        "embedding": round(embedding, 6),
        "external": round(external, 6),
        "total": round(llm + embedding + external, 6),
    }