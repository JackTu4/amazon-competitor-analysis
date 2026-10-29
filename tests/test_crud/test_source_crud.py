import pytest

pytestmark = pytest.mark.integration

from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.db.crud.project import create_project
from backend.app.db.crud.product import create_product
from backend.app.db.crud.source import (
    create_source,
    get_source,
    list_sources_by_product,
    update_source,
    delete_source,
)


def test_source_crud():
    task_id = str(uuid4())

    with SessionLocal() as db:
        try:
            # 1. 创建分析项目
            create_project(
                db=db,
                task_id=task_id,
                target_product="HUADISK SSD 256GB",
            )

            # 2. 创建目标商品
            product = create_product(
                db=db,
                task_id=task_id,
                role="target",
                name="HUADISK SSD 256GB",
                asin="B0FFHBN5ZQ",
            )

            product_id = product.id

            # 3. 创建两条数据来源
            source_1 = create_source(
                db=db,
                product_id=product_id,
                source_url=(
                    "https://www.amazon.com/dp/B0FFHBN5ZQ"
                ),
                source_type="amazon",
            )

            source_2 = create_source(
                db=db,
                product_id=product_id,
                source_url="https://example.com/product-info",
                source_type="web_search",
            )

            source_1_id = source_1.id
            source_2_id = source_2.id

            # 4. 查询单条来源
            saved = get_source(db, source_1_id)

            assert saved is not None
            assert saved.product_id == product_id
            assert saved.source_type == "amazon"

            print("创建和查询来源成功")

            # 5. 查询商品的所有来源
            sources = list_sources_by_product(
                db=db,
                product_id=product_id,
            )

            assert len(sources) == 2

            print("商品关联来源成功")

            # 6. 更新来源类型
            update_source(
                db=db,
                source_id=source_2_id,
                source_type="product_page",
            )

            updated = get_source(db, source_2_id)

            assert updated.source_type == "product_page"

            print("更新来源成功")

            # 7. 删除第二条来源
            assert delete_source(db, source_2_id)

            sources = list_sources_by_product(db, product_id)

            assert len(sources) == 1

            print("删除来源成功")

        finally:
            # 回滚整个测试事务
            # 不在数据库中保留测试数据
            db.rollback()
