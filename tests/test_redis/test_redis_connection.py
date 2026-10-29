import pytest

pytestmark = pytest.mark.integration

import redis


def test_redis_connection():
    # 1. 创建 Redis 客户端
    client = redis.Redis(
        host="127.0.0.1",
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )

    # 2. 测试连接
    assert client.ping() is True

    # 3. 写入测试数据
    client.set("agent:test", "hello redis", ex=60)

    # 4. 读取测试数据
    result = client.get("agent:test")

    assert result == "hello redis"

    # 5. 删除测试数据
    client.delete("agent:test")

    print("Redis 连接、写入、读取测试成功")