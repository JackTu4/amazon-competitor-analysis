from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from evals import framework

EVALS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVALS_DIR.parent

ENV_PATH = PROJECT_ROOT / ".env"
CASES_PATH = EVALS_DIR / "cases.json"
PRICING_PATH = EVALS_DIR / "pricing.json"
REQUIRED_ENV = (
    "OPENAI_API_KEY",
    "OPENAI_API_URL",
    "TAVILY_API_KEY",
    "BRIGHTDATA_API_KEY",
    "EMBEDDING_MODEL",
    "DB_HOST",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
)
REQUIRED_TABLES = {"projects", "products", "sources", "reports"}


def report(name: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}{('：' + detail) if detail else ''}")
    return ok


def check_env_file() -> bool:
    path = ENV_PATH
    return report(".env 存在", path.is_file(), str(path))


def check_env_keys() -> bool:
    missing = [key for key in REQUIRED_ENV if not os.getenv(key)]
    return report(
        ".env 必需项齐全",
        not missing,
        "缺少 " + ", ".join(missing) if missing else f"{len(REQUIRED_ENV)} 项都有值",
    )


def check_mock_switch() -> bool:
    from backend.app.services import analysis_service

    analysis_service.MOCK_MODE = False

    return report(
        "MOCK_MODE 可强制关闭",
        analysis_service.MOCK_MODE is False,
        "当前为 False，会走真实工作流",
    )


def check_database() -> bool:
    from sqlalchemy import inspect, text

    from backend.app.db.database import engine

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    tables = set(inspect(engine).get_table_names())
    missing = REQUIRED_TABLES - tables

    if missing:
        return report(
            "MySQL 可连接且表结构完整",
            False,
            "缺少表 " + ", ".join(sorted(missing))
            + "；先执行 python -m backend.app.db.init_db",
        )

    return report("MySQL 可连接且表结构完整", True, "4 张表都在")


def check_reports_dir() -> bool:
    path = framework.PROJECT_ROOT / "reports"
    path.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        dir=path,
        prefix=".eval-check-",
        suffix=".tmp",
        delete=True,
    ):
        pass

    return report("reports/ 可写", True, str(path))


def check_cases() -> bool:
    cases = framework.load_cases()
    ok = report("cases.json 可解析", True, f"{len(cases)} 个案例")

    if not ok:
        return False

    unfinished = []

    for case in cases:
        expected = case.get("expected", {})
        missing = [
            field
            for field in ("target_asin", "price", "rating", "reviews")
            if expected.get(field) in (None, "")
        ]

        if missing:
            unfinished.append(f"{case['id']}（缺 {', '.join(missing)}）")

    if unfinished:
        print("  注意：以下案例的预期值还没填，跑之前先补齐，否则这些字段不计分：")
        for item in unfinished:
            print(f"    - {item}")

    return ok


def check_pricing() -> bool:
    pricing = framework.load_pricing()
    zero = [
        key
        for key, value in pricing.items()
        if key.endswith(("_per_1m", "_per_search", "_per_job"))
        and not float(value)
    ]

    detail = "全部单价为 0，成本会显示 0" if zero else "单价已填写"

    return report("pricing.json 可解析", True, detail)


def main() -> int:
    load_dotenv(framework.PROJECT_ROOT / ".env")
    os.chdir(framework.PROJECT_ROOT)
    framework.ensure_dirs()

    print("== 评估环境自检 ==\n")

    checks = [
        ("env_file", check_env_file),
        ("env_keys", check_env_keys),
        ("mock", check_mock_switch),
        ("db", check_database),
        ("reports", check_reports_dir),
        ("cases", check_cases),
        ("pricing", check_pricing),
    ]

    passed = 0

    for _, func in checks:
        try:
            passed += int(bool(func()))
        except Exception as exc:
            report(func.__name__, False, f"{type(exc).__name__}: {exc}")

    print(f"\n自检结果：{passed}/{len(checks)} 通过")

    if passed != len(checks):
        print("修完再跑评估，否则跑出来的数据不可信。")
        return 1

    print("可以开始跑评估：python -m evals.run_eval --case case-01")
    return 0


if __name__ == "__main__":
    sys.exit(main())