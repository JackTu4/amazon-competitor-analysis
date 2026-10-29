from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import ProductRecord, SourceRecord


def create_product(
    db: Session,
    task_id: str,
    role: str,
    name: str | None = None,
    title: str | None = None,
    asin: str | None = None,
    brand: str | None = None,
    price: Decimal | None = None,
    currency: str | None = None,
    rating: float | None = None,
    reviews: int | None = None,
) -> ProductRecord:
    """创建商品记录。"""

    if role not in ("target", "competitor"):
        raise ValueError("role 必须是 target 或 competitor")

    product = ProductRecord(
        task_id=task_id,
        role=role,
        name=name,
        title=title,
        asin=asin,
        brand=brand,
        price=price,
        currency=currency,
        rating=rating,
        reviews=reviews,
    )

    db.add(product)
    db.flush()

    return product


def get_product(
    db: Session,
    product_id: int,
) -> ProductRecord | None:
    """根据商品记录 ID 查询商品。"""

    return db.get(ProductRecord, product_id)


def list_products_by_task(
    db: Session,
    task_id: str,
) -> list[ProductRecord]:
    """查询一个分析任务下的所有商品。"""

    stmt = (
        select(ProductRecord)
        .where(ProductRecord.task_id == task_id)
        .order_by(ProductRecord.id)
    )

    return list(db.scalars(stmt).all())


def delete_products_by_task(
    db: Session,
    task_id: str,
) -> int:
    """删除一个任务下的全部商品及其来源，返回删除的商品数。

    用于任务重跑时先清空旧明细，保证写入幂等。
    """

    product_ids = [
        product.id
        for product in list_products_by_task(db, task_id)
    ]

    if product_ids:
        (
            db.query(SourceRecord)
            .filter(SourceRecord.product_id.in_(product_ids))
            .delete(synchronize_session=False)
        )

    deleted = (
        db.query(ProductRecord)
        .filter(ProductRecord.task_id == task_id)
        .delete(synchronize_session=False)
    )

    db.flush()

    return deleted


def update_product(
    db: Session,
    product_id: int,
    **fields,
) -> ProductRecord | None:
    """更新商品字段。"""

    product = get_product(db, product_id)

    if product is None:
        return None

    allowed_fields = {
        "name",
        "title",
        "asin",
        "brand",
        "price",
        "currency",
        "rating",
        "reviews",
    }

    for key, value in fields.items():
        if key not in allowed_fields:
            raise ValueError(f"不允许修改字段：{key}")

        setattr(product, key, value)

    db.flush()

    return product


def delete_product(
    db: Session,
    product_id: int,
) -> bool:
    """删除商品记录。"""

    product = get_product(db, product_id)

    if product is None:
        return False

    db.delete(product)
    db.flush()

    return True
