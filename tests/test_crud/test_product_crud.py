import pytest

pytestmark = pytest.mark.integration

from decimal import Decimal
from uuid import uuid4

from backend.app.db.database import SessionLocal
from backend.app.db.crud.project import create_project
from backend.app.db.crud.product import (
    create_product,
    get_product,
    list_products_by_task,
    update_product,
    delete_product,
)
from backend.app.db.models import Project


def test_product_crud():
    task_id = str(uuid4())

    with SessionLocal() as db:
        try:
            # 1. 先创建所属项目
            create_project(
                db=db,
                task_id=task_id,
                target_product="HUADISK SSD 256GB",
            )

            # 2. 创建目标商品
            target = create_product(
                db=db,
                task_id=task_id,
                role="target",
                name="HUADISK SSD 256GB",
                asin="B0FFHBN5ZQ",
                price=Decimal("50.99"),
                currency="USD",
                rating=4.4,
            )

            # 3. 创建两个竞品
            competitor_1 = create_product(
                db=db,
                task_id=task_id,
                role="competitor",
                name="KingSpec SSD",
            )

            competitor_2 = create_product(
                db=db,
                task_id=task_id,
                role="competitor",
                name="Samsung SSD",
            )

            target_id = target.id
            competitor_1_id = competitor_1.id
            competitor_2_id = competitor_2.id

            db.flush()

            # 4. 查询商品
            saved_target = get_product(db, target_id)

            assert saved_target is not None
            assert saved_target.role == "target"
            assert saved_target.price == Decimal("50.99")

            print("创建和查询商品成功")

            # 5. 查询当前任务的所有商品
            products = list_products_by_task(db, task_id)

            assert len(products) == 3
            assert sum(p.role == "target" for p in products) == 1
            assert sum(p.role == "competitor" for p in products) == 2

            print("项目关联商品成功")

            # 6. 更新竞品信息
            update_product(
                db=db,
                product_id=competitor_1_id,
                asin="B0D1R7HDJF",
                rating=4.5,
            )

            updated = get_product(db, competitor_1_id)

            assert updated.asin == "B0D1R7HDJF"
            assert updated.rating == 4.5

            print("更新商品成功")

            # 7. 删除一个竞品
            assert delete_product(db, competitor_2_id)

            products = list_products_by_task(db, task_id)

            assert len(products) == 2

            print("删除商品成功")

        finally:
            # 本测试所有写入都在同一个事务中
            # 最后回滚，避免留下测试数据
            db.rollback()