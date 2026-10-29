import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import router


# 1. 读取项目根目录的 .env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def get_allowed_origins() -> list[str]:
    """从 ALLOWED_ORIGINS 读取允许的跨域来源，逗号分隔。"""

    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )

    return [
        origin.strip()
        for origin in raw.split(",")
        if origin.strip()
    ]


# 2. 创建 FastAPI 应用
app = FastAPI(
    title="Amazon 智能竞品分析系统",
    description="提供商品竞品分析任务和报告查询接口",
    version="0.1.0",
)

# 3. 配置跨域：只放行白名单来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 4. 注册分析业务路由
app.include_router(router)


# 5. 健康检查（不鉴权，供探活使用）
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Amazon 竞品分析后端运行正常",
    }
