from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import SourceRecord


def create_source(
    db: Session,
    product_id: int,
    source_url: str,
    source_type: str | None = None,
) -> SourceRecord:
    """创建商品数据来源记录。"""

    if not source_url.strip():
        raise ValueError("source_url 不能为空")

    source = SourceRecord(
        product_id=product_id,
        source_url=source_url.strip(),
        source_type=source_type,
    )

    db.add(source)
    db.flush()

    return source


def get_source(
    db: Session,
    source_id: int,
) -> SourceRecord | None:
    """根据来源 ID 查询记录。"""

    return db.get(SourceRecord, source_id)


def list_sources_by_product(
    db: Session,
    product_id: int,
) -> list[SourceRecord]:
    """查询指定商品的全部数据来源。"""

    stmt = (
        select(SourceRecord)
        .where(SourceRecord.product_id == product_id)
        .order_by(SourceRecord.id)
    )

    return list(db.scalars(stmt).all())


def update_source(
    db: Session,
    source_id: int,
    source_url: str | None = None,
    source_type: str | None = None,
) -> SourceRecord | None:
    """更新来源记录。"""

    source = get_source(db, source_id)

    if source is None:
        return None

    if source_url is not None:
        if not source_url.strip():
            raise ValueError("source_url 不能为空")
        source.source_url = source_url.strip()

    if source_type is not None:
        source.source_type = source_type

    db.flush()

    return source


def delete_source(
    db: Session,
    source_id: int,
) -> bool:
    """删除来源记录。"""

    source = get_source(db, source_id)

    if source is None:
        return False

    db.delete(source)
    db.flush()

    return True