"""批量运行全部案例：每个案例独立子进程，跑完自动汇总。

用法：
    python -m evals.run_all
    python -m evals.run_all --only case-01,case-02
    python -m evals.run_all --force
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

from evals import framework


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量运行评估案例")
    parser.add_argument(
        "--only",
        default="",
        help="只跑指定案例，逗号分隔，例如 case-01,case-02",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="已存在结果也重跑",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="单个案例超时秒数，默认 1800",
    )
    parser.add_argument(
        "--sleep",
        type=int,
        default=5,
        help="两个案例之间的间隔秒数，默认 5",
    )
    return parser.parse_args()


def selected_cases(only: str) -> list[dict]:
    cases = framework.load_cases()

    if not only.strip():
        return cases

    wanted = {item.strip() for item in only.split(",") if item.strip()}
    chosen = [case for case in cases if case["id"] in wanted]
    missing = wanted - {case["id"] for case in chosen}

    if missing:
        raise SystemExit(f"cases.json 里没有这些 id：{sorted(missing)}")

    return chosen


def main() -> int:
    args = parse_args()
    cases = selected_cases(args.only)

    framework.ensure_dirs()

    failed: list[str] = []
    skipped: list[str] = []

    for index, case in enumerate(cases, start=1):
        case_id = case["id"]
        result_path = framework.RESULTS_DIR / f"{case_id}.json"

        if result_path.exists() and not args.force:
            skipped.append(case_id)
            print(f"[{index}/{len(cases)}] 跳过 {case_id}：结果已存在")
            continue

        print(f"[{index}/{len(cases)}] 运行 {case_id}：{case['target_product']}")

        command = [
            sys.executable,
            "-m",
            "evals.run_eval",
            "--case",
            case_id,
            "--force",
        ]

        try:
            completed = subprocess.run(
                command,
                cwd=framework.PROJECT_ROOT,
                timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            print(f"  -> 超时（>{args.timeout}s）")
            failed.append(case_id)
            continue

        if completed.returncode != 0:
            failed.append(case_id)

        if index < len(cases):
            time.sleep(args.sleep)

    print("\n完成。")
    print(f"跑完：{len(cases) - len(skipped)} 个，跳过：{len(skipped)} 个")

    if failed:
        print(f"未通过或异常：{', '.join(failed)}")

    print("下一步：python -m evals.summarize")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())