"""单个评估案例的运行器：真实模式跑一次完整分析，评分后落盘。

用法：
    python -m evals.run_eval --case case-01
    python -m evals.run_eval --case case-01 --force
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from evals import framework

logger = logging.getLogger("evals.run_eval")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行单个评估案例")
    parser.add_argument("--case", required=True, help="案例 id，例如 case-01")
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已存在的结果文件",
    )
    return parser.parse_args()


def find_case(cases: list[dict], case_id: str) -> dict:
    for case in cases:
        if case["id"] == case_id:
            return case

    raise SystemExit(
        f"找不到案例 {case_id}，可用："
        + ", ".join(case["id"] for case in cases)
    )


def resolve_report_path(raw: str | None) -> Path | None:
    if not raw:
        return None

    path = Path(raw)

    if not path.is_absolute():
        path = framework.PROJECT_ROOT / path

    return path


def read_report(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""

    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        logger.exception("读取报告失败：%s", path)
        return ""


def judge(
    case: dict,
    status: str | None,
    error: str | None,
    report_text: str,
    competitor_score: dict,
) -> tuple[bool, list[str]]:
    expect_success = bool(case.get("expect", {}).get("success", True))
    reasons: list[str] = []

    if not expect_success:
        if status != "failed":
            reasons.append(f"预期失败，实际状态为 {status}")

        if not error:
            reasons.append("预期失败，但没有错误信息")

        return not reasons, reasons

    if status != "completed":
        reasons.append(f"任务未完成，状态为 {status}")

    if not report_text.strip():
        reasons.append("报告为空或文件不存在")

    if "（模拟）" in report_text:
        reasons.append("报告是 MOCK 产物，说明没有真正走真实工作流")

    min_valid = int(case.get("expected", {}).get("min_valid_competitors", 0))

    if competitor_score["valid_count"] < min_valid:
        reasons.append(
            f"有效竞品 {competitor_score['valid_count']} 个，"
            f"少于预期 {min_valid} 个"
        )

    return not reasons, reasons


def main() -> int:
    args = parse_args()

    cases = framework.load_cases()
    case = find_case(cases, args.case)
    case_id = case["id"]

    framework.ensure_dirs()
    setup_log_path = framework.setup_logging(case_id)

    result_path = framework.RESULTS_DIR / f"{case_id}.json"

    if result_path.exists() and not args.force:
        print(
            f"结果已存在：{result_path}\n"
            "如需覆盖请加 --force"
        )
        return 1

    # 1. 读 .env，并固定工作目录（报告写入 reports/ 相对路径）
    load_dotenv(framework.PROJECT_ROOT / ".env")
    os.chdir(framework.PROJECT_ROOT)

    # 2. 强制真实模式：MOCK_MODE 在 import 时按环境变量取值，默认 true
    from backend.app.services import analysis_service

    analysis_service.MOCK_MODE = False

    if analysis_service.MOCK_MODE is not False:
        raise SystemExit("MOCK_MODE 未能切换为 False，评估无效")

    # 3. 装上计量补丁
    tracker = framework.UsageTracker()
    tracker.install()

    from backend.app.services.result_service import get_analysis_products
    from backend.app.services.task_service import (
        create_task_record,
        get_analysis_task,
    )

    pricing = framework.load_pricing()
    expected = case.get("expected", {})

    task_id = str(uuid4())
    started_at = datetime.now(timezone.utc)
    logger.info("=== 案例 %s 开始，task_id=%s ===", case_id, task_id)
    logger.info("目标商品：%s", case["target_product"])

    create_task_record(
        task_id=task_id,
        target_product=case["target_product"],
    )

    error: str | None = None
    trace: str | None = None
    start_clock = time.perf_counter()

    try:
        analysis_service.run_analysis(task_id, case["target_product"])
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        trace = traceback.format_exc()
        logger.exception("案例 %s 运行失败", case_id)

    duration = round(time.perf_counter() - start_clock, 2)

    # 4. 读结果：任务状态、商品明细、报告
    record = get_analysis_task(task_id) or {}
    products = get_analysis_products(task_id)
    status = record.get("status")
    result_field = record.get("result")

    if not error and record.get("error"):
        error = str(record["error"])

    report_path = resolve_report_path(result_field)
    report_text = read_report(report_path)

    target = next(
        (product for product in products if product.get("role") == "target"),
        None,
    )
    competitors = [
        product for product in products if product.get("role") == "competitor"
    ]

    target_checks = framework.target_field_checks(expected, target)
    target_rate = framework.rate_checks(target_checks)
    competitor_score = framework.score_competitors(competitors, target, expected)
    completeness_rate = framework.completeness(products)
    usage = tracker.snapshot()
    cost = framework.compute_cost(usage, pricing)

    success, reasons = judge(
        case=case,
        status=status,
        error=error,
        report_text=report_text,
        competitor_score=competitor_score,
    )

    notes = []

    if status == "completed" and not products:
        notes.append(
            "任务完成但商品明细为空：可能落库失败被吞掉了，查日志确认"
        )

    result = {
        "case_id": case_id,
        "case_type": case.get("type", "positive"),
        "target_product": case["target_product"],
        "note": case.get("note", ""),
        "task_id": task_id,
        "started_at": started_at.isoformat(),
        "duration_seconds": duration,
        "status": status,
        "error": error,
        "success": success,
        "failure_reasons": reasons,
        "notes": notes,
        "expected": expected,
        "actual": {
            "target": target,
            "competitors": competitors,
            "product_count": len(products),
        },
        "scores": {
            "target_field_checks": target_checks,
            "target_field_accuracy": target_rate,
            "competitor": competitor_score,
            "completeness": round(completeness_rate, 4),
        },
        "report": {
            "path": str(report_path) if report_path else None,
            "exists": bool(report_text),
            "chars": len(report_text),
            "sections": framework.report_sections(report_text),
            "has_failure_appendix": "未完成分析的竞品" in report_text,
        },
        "usage": usage,
        "cost_usd": cost,
        "runtime": {
            "python": platform.python_version(),
            "llm_model": os.getenv("LLM_MODEL_NAME", "qwen3.7-flash"),
            "embedding_model": os.getenv("EMBEDDING_MODEL"),
            "mock_mode": analysis_service.MOCK_MODE,
            "git": framework.git_state(),
            "pricing": pricing,
            "log_path": str(setup_log_path),
        },
    }

    if trace:
        result["traceback"] = trace

    framework.write_json(result_path, result)

    logger.info(
        "=== 案例 %s 结束：success=%s status=%s 耗时=%ss 成本=$%s ===",
        case_id,
        success,
        status,
        duration,
        cost["total"],
    )

    if not success:
        for reason in reasons:
            logger.warning("失败原因：%s", reason)

    print(f"结果已写入 {result_path}")
    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())