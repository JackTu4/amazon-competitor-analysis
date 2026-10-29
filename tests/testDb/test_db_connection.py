import pytest

pytestmark = pytest.mark.integration

from backend.app.db.database import engine
from sqlalchemy import text

def test_mysql_connection():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DATABASE()")
        )

        database_name = result.scalar_one()

        assert database_name == "competitor_analysis"

        print("MySQL 连接成功")
        print("当前数据库：", database_name)
