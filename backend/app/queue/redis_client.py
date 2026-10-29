
import os

from redis import Redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0",
)


def get_redis_connection() -> Redis:
    """创建 Redis 连接客户端。"""

    return Redis.from_url(
        REDIS_URL,
        socket_connect_timeout=5,
        socket_timeout=5,
    )