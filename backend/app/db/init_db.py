"""数据库初始化：创建库与表结构。"""

import logging

import pymysql

from backend.app.db import models  # noqa: F401  导入模型以注册到 Base.metadata
from backend.app.db import database

logger = logging.getLogger(__name__)


def create_database_if_missing() -> None:
    """库不存在时自动创建（utf8mb4）。"""

    connection = pymysql.connect(
        host=database.DB_HOST,
        port=database.DB_PORT,
        user=database.DB_USER,
        password=database.DB_PASSWORD,
        charset="utf8mb4",
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database.DB_NAME}` "
                "CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci"
            )

        connection.commit()
    finally:
        connection.close()

    logger.info("数据库已就绪：%s", database.DB_NAME)


def init_db() -> list[str]:
    """创建所有 ORM 模型对应的表，返回表名列表。"""

    create_database_if_missing()

    database.Base.metadata.create_all(bind=database.engine)

    return sorted(database.Base.metadata.tables)
