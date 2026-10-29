"""汇总 results/case-*.json，生成 summary.csv 与 report.md。

用法：
    python -m evals.summarize
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from statistics import mean

from evals import framework

CSV_FIELDS = [
    "case_id",
    "case_type",
    "target_product",
    "status",
    "success",
    "duration_seconds",
    "target_field_accuracy",
    "competitor_rate",
    "valid_competitors",
    "product_count",
    "completeness",
    "llm_calls",
    "prompt_tokens",
    "completion_tokens",
    "embedding_tokens",
    "tavily_calls",
    "brightdata_jobs",
    "cost_usd",
    "failure_reasons",
]


def format_number(value: float | None, digits: int = 3) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def load_results() -> list[dict]:
    files = sorted(framework.RESULTS_DIR.glob("case-*.json"))
    results = []

    for path in files:
        try:
            results.append(framework.load_json(path))
        except Exception:
            print(f"跳过无法解析的文件：{path}")

    return results


def row_of(result: dict) -> dict:
    scores = result.get("scores", {})
    usage = result.get("usage", {})
    competitor = scores.get("competitor", {})

    return {
        "case_id": result.get("case_id"),
        "case_type": result.get("case_type"),
        "target_product": result.get("target_product"),
        "status": result.get("status"),
        "success": "通过" if result.get("success") else "未通过",
        "duration_seconds": format_number(result.get("duration_seconds"), 1),
        "target_field_accuracy": format_number(
            scores.get("target_field_accuracy")
        ),
        "competitor_rate": format_number(competitor.get("rate")),
        "valid_competitors": competitor.get("valid_count"),
        "product_count": result.get("actual", {}).get("product_count"),
        "completeness": format_number(scores.get("completeness")),
        "llm_calls": usage.get("llm_calls", 0),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "embedding_tokens": usage.get("embedding_tokens", 0),
        "tavily_calls": usage.get("tavily_calls", 0),
        "brightdata_jobs": usage.get("brightdata_jobs", 0),
        "cost_usd": format_number(result.get("cost_usd", {}).get("total"), 4),
        "failure_reasons": "；".join(result.get("failure_reasons", [])),
    }


def write_csv(results: list[dict]) -> None:
    path = framework.RESULTS_DIR / "summary.csv"

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for result in results:
            writer.writerow(row_of(result))

    print(f"已写入 {path}")


def aggregate(results: list[dict]) -> dict:
    positive = [
        result for result in results if result.get("case_type") == "positive"
    ]

    def average(values: list[float]) -> float | None:
        return mean(values) if values else None

    target_rates = [
        result["scores"]["target_field_accuracy"]
        for result in positive
        if result.get("scores", {}).get("target_field_accuracy") is not None
    ]

    durations = [result.get("duration_seconds", 0) for result in results]
    costs = [result.get("cost_usd", {}).get("total", 0) for result in results]

    return {
        "total": len(results),
        "positive": len(positive),
        "negative": len(results) - len(positive),
        "passed": sum(1 for result in results if result.get("success")),
        "success_rate": (
            sum(1 for result in results if result.get("success")) / len(results)
            if results
            else 0.0
        ),
        "target_accuracy": average(target_rates),
        "competitor_rate": average([
            result["scores"]["competitor"]["rate"]
            for result in positive
            if result.get("scores", {}).get("competitor")
        ]),
        "completeness": average([
            result["scores"]["completeness"]
            for result in results
            if result.get("scores", {}).get("completeness") is not None
        ]),
        "avg_duration": average(durations),
        "total_cost": sum(costs),
        "avg_cost": average(costs),
    }


def write_report(results: list[dict], stats: dict) -> None:
    runtime = results[0].get("runtime", {}) if results else {}
    git = runtime.get("git", {})
    lines: list[str] = []

    lines.append("# Amazon 竞品分析系统 · 评估报告")
    lines.append("")
    lines.append(
        f"- 生成时间：{datetime.now(timezone.utc).isoformat()}（UTC）"
    )
    lines.append(
        f"- 代码版本：`{git.get('commit') or '未知'}`"
        f"（未提交改动 {git.get('changed_files', 0)} 个文件，"
        f"{'dirty' if git.get('dirty') else 'clean'}）"
    )
    lines.append(
        f"- 模型：`{runtime.get('llm_model') or '未知'}`，"
        f"Embedding：`{runtime.get('embedding_model') or '未知'}`"
    )
    lines.append("- 运行模式：真实模式（MOCK_MODE=False）")
    lines.append("")

    lines.append("## 汇总")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("| --- | --- |")
    lines.append(f"| 案例数 | {stats['total']}（正向 {stats['positive']} / 负向 {stats['negative']}） |")
    lines.append(
        f"| 任务成功率 | {stats['passed']}/{stats['total']}"
        f" = {stats['success_rate'] * 100:.1f}% |"
    )
    lines.append(
        "| 目标字段准确率（正向均值） | "
        f"{format_number(stats['target_accuracy'])} |"
    )
    lines.append(
        "| 竞品有效性得分（正向均值） | "
        f"{format_number(stats['competitor_rate'])} |"
    )
    lines.append(
        f"| 信息完整度（全部均值） | {format_number(stats['completeness'])} |"
    )
    lines.append(
        "| 平均耗时 | "
        f"{format_number(stats['avg_duration'], 1)} 秒 |"
    )
    lines.append(
        "| API 总成本 | "
        f"${format_number(stats['total_cost'], 4)}"
        f"（单案例均值 ${format_number(stats['avg_cost'], 4)}） |"
    )
    lines.append("")

    lines.append("## 逐案例")
    lines.append("")
    lines.append(
        "| 案例 | 商品 | 类型 | 状态 | 通过 | 耗时(s) | "
        "目标准确率 | 竞品得分 | 有效竞品 | 成本($) |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")

    for result in results:
        row = row_of(result)
        lines.append(
            f"| {row['case_id']} | {row['target_product']} | "
            f"{row['case_type']} | {row['status']} | {row['success']} | "
            f"{row['duration_seconds']} | {row['target_field_accuracy']} | "
            f"{row['competitor_rate']} | {row['valid_competitors']} | "
            f"{row['cost_usd']} |"
        )

    lines.append("")

    failed = [result for result in results if not result.get("success")]

    lines.append("## 未通过的案例")
    lines.append("")

    if not failed:
        lines.append("无。")
    else:
        for result in failed:
            lines.append(f"### {result.get('case_id')} · {result.get('target_product')}")
            lines.append("")

            for reason in result.get("failure_reasons", []):
                lines.append(f"- {reason}")

            if result.get("error"):
                lines.append(f"- 异常：`{result['error']}`")

            for note in result.get("notes", []):
                lines.append(f"- 备注：{note}")

            lines.append("")

    lines.append("## 结论（需人工填写）")
    lines.append("")
    lines.append("> 自动生成的部分到此为止。下面的结论只能由你根据上表自己写。")
    lines.append("")
    lines.append("- 系统在哪些商品类目上表现稳定：")
    lines.append("- 最明显的失败模式是什么（字段错、竞品偏、超时、成本高）：")
    lines.append("- 一条可以写进简历、且有数据支撑的结论：")
    lines.append("")

    lines.append("## 这份评估不能证明什么")
    lines.append("")
    lines.append("- 案例数只有 10 个，是抽样检查，不是统计意义上的基准测试。")
    lines.append("- 预期值来自人工录入的 Amazon 页面，价格和评论数会随时间变化，"
                 "同一案例隔几周重跑可能不再一致。")
    lines.append("- 竞品只按 ASIN 格式、去重、品牌差异、类目关键词判定，"
                 "没有人工判断“是否真的好用”。")
    lines.append("- 成本是本地按单价估算的，不是账单金额；单价见 "
                 "`evals/pricing.json`。")
    lines.append("- 真实用户场景下的并发、稳定性和数据规模都没有覆盖。")
    lines.append("")

    path = framework.RESULTS_DIR / "report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已写入 {path}")


def main() -> int:
    results = load_results()

    if not results:
        print("results/ 下没有 case-*.json，先跑 evals.run_eval 或 evals.run_all")
        return 1

    stats = aggregate(results)
    write_csv(results)
    write_report(results, stats)

    print(
        f"通过 {stats['passed']}/{stats['total']}，"
        f"平均目标准确率 {format_number(stats['target_accuracy'])}，"
        f"总成本 ${format_number(stats['total_cost'], 4)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())