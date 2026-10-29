import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# 1. 定位项目根目录并读取 .env
BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(BASE_DIR / ".env")


# 2. 读取数据库配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "competitor_analysis")

if not DB_PASSWORD:
    raise RuntimeError("缺少 DB_PASSWORD，请检查项目根目录的 .env 文件")


# 3. 构建数据库连接地址
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    query={"charset": "utf8mb4"},
)


# 4. 创建 SQLAlchemy 数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)


# 5. 创建 Session 工厂
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


# 6. ORM 模型基类
class Base(DeclarativeBase):
    pass

# 7. FastAPI 数据库 Session 依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()