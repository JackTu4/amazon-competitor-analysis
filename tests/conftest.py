"""pytest 全局配置。

项目里部分模块在导入时就会构造外部客户端（OpenAI / Tavily），
并且 `backend/app/db/database.py` 要求 DB_PASSWORD 存在。
没有 .env 的环境（CI、刚 clone 的仓库）里，这里先补占位值，
让不访问外部服务的单元测试能正常导入和运行。

真正需要连库或调用大模型的测试请显式指定：
    pytest -m integration   （需要 .env + 本地 MySQL/Redis）
    pytest -m llm           （需要真实密钥，会产生费用）
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

PLACEHOLDERS = {
    "DB_PASSWORD": "test-only-placeholder",
    "OPENAI_API_KEY": "sk-test-only-placeholder",
    "OPENAI_API_URL": "http://127.0.0.1:1/v1",
    "TAVILY_API_KEY": "tvly-test-only-placeholder",
    "BRIGHTDATA_API_KEY": "test-only-placeholder",
    "BRIGHTDATA_DATASET_ID": "test-only-placeholder",
    "EMBEDDING_MODEL": "test-embedding-model",
}

if not ENV_FILE.exists():
    for key, value in PLACEHOLDERS.items():
        os.environ.setdefault(key, value)
