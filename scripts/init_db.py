"""初始化 MySQL 库与表结构。

用法：
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# 允许直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db.init_db import init_db  # noqa: E402


def main() -> None:
    tables = init_db()

    print("数据库初始化完成，以下数据表已就绪：")

    for name in tables:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
