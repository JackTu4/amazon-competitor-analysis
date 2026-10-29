import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader


# 1. 读取项目根目录的 .env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)


# 2. 读取 API Key 配置
API_KEY = os.getenv("API_KEY", "").strip()

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="在项目根目录 .env 中配置 API_KEY 后，请求需携带该请求头",
)

if not API_KEY:
    logger.warning(
        "未配置 API_KEY，/api 接口鉴权已关闭（仅适合本机开发）"
    )


def require_api_key(
    api_key: str | None = Security(api_key_header),
) -> None:
    """校验请求头中的 API Key；未配置 API_KEY 时放行。"""

    # 1. 未配置密钥：本机开发模式，不启用鉴权
    if not API_KEY:
        return

    # 2. 使用常数时间比较，避免时序攻击
    if api_key and secrets.compare_digest(api_key, API_KEY):
        return

    # 3. 缺失或不匹配统一返回 401
    raise HTTPException(
        status_code=401,
        detail="无效或缺失的 API Key",
        headers={"WWW-Authenticate": "APIKey"},
    )
