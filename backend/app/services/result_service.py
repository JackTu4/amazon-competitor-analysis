"""把工作流产出的商品明细落库，并提供查询。"""

import logging
from decimal import Decimal, InvalidOperation

from app.models.competitor import CompetitorAnalysis
from app.workflow.result import WorkflowResult

from backend.app.db.crud.product import (
    create_product,
    delete_products_by_task,
    list_products_by_task,
)
from backend.app.db.crud.source import create_source
from backend.app.db.database import SessionLocal

logger = logging.getLogger(__name__)


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_analysis(raw) -> CompetitorAnalysis | None:
    """把工作流结果里的 analysis 统一成 CompetitorAnalysis。"""

    if isinstance(raw, CompetitorAnalysis):
        return raw

    if isinstance(raw, dict) and not raw.get("error"):
        try:
            return CompetitorAnalysis(**raw)
        except Exception:
            logger.warning("分析结果无法转换为模型，跳过落库", exc_info=True)

    return None


def _save_source(db, product_id: int, url: str | None) -> None:
    if not url or not url.strip():
        return

    source_type = "amazon" if "amazon." in url.lower() else "web"

    create_source(
        db=db,
        product_id=product_id,
        source_url=url,
        source_type=source_type,
    )


def _save_product(
    db,
    task_id: str,
    role: str,
    product_analysis,
    name: str | None = None,
    asin: str | None = None,
):
    """把一个 ProductAnalysis 写成 ProductRecord。"""

    product = product_analysis.product
    price = product_analysis.price

    return create_product(
        db=db,
        task_id=task_id,
        role=role,
        name=name or product.name,
        title=product.title,
        asin=asin or product.asin,
        brand=product.brand,
        price=_to_decimal(price.amount) if price else None,
        currency=price.currency if price else None,
        rating=product_analysis.rating,
        reviews=product_analysis.reviews,
    )


def save_analysis_results(
    task_id: str,
    result: WorkflowResult,
) -> int:
    """保存目标任务下的目标商品、竞品及其来源，返回写入的商品数。

    重跑任务时会先清空旧明细，保证幂等。
    """

    converted = []

    for item in result.analyses or []:
        analysis = _to_analysis(item.get("analysis"))

        if analysis is not None:
            converted.append((item, analysis))

    if not converted:
        logger.info("没有可落库的商品明细，task_id=%s", task_id)
        return 0

    with SessionLocal() as db:
        try:
            delete_products_by_task(db, task_id)

            # 目标商品在所有分析里重复出现，只落一条
            _, first_analysis = converted[0]
            target_record = _save_product(
                db=db,
                task_id=task_id,
                role="target",
                product_analysis=first_analysis.target_product,
                name=(
                    first_analysis.target_product.product.name
                    or result.target_product
                    or None
                ),
            )

            target_asin = (
                first_analysis.target_product.product.asin
                or result.target_asin
            )

            if target_asin:
                _save_source(
                    db,
                    target_record.id,
                    f"https://www.amazon.com/dp/{target_asin}",
                )

            for item, analysis in converted:
                competitor = analysis.competitor

                record = _save_product(
                    db=db,
                    task_id=task_id,
                    role="competitor",
                    product_analysis=competitor,
                    name=item.get("competitor_name") or competitor.product.name,
                    asin=item.get("competitor_asin") or competitor.product.asin,
                )

                url = item.get("competitor_url")

                if not url and record.asin:
                    url = f"https://www.amazon.com/dp/{record.asin}"

                _save_source(db, record.id, url)

            db.commit()

        except Exception:
            db.rollback()
            logger.exception("保存分析明细失败，task_id=%s", task_id)
            raise

    count = 1 + len(converted)

    logger.info(
        "分析明细已落库，task_id=%s，商品数=%s，失败竞品数=%s",
        task_id,
        count,
        len(result.failures),
    )

    return count


def get_analysis_products(task_id: str) -> list[dict]:
    """查询一个任务下已落库的商品明细。"""

    with SessionLocal() as db:
        products = list_products_by_task(db, task_id)

        return [
            {
                "product_id": product.id,
                "role": product.role,
                "name": product.name,
                "title": product.title,
                "asin": product.asin,
                "brand": product.brand,
                "price": (
                    float(product.price)
                    if product.price is not None
                    else None
                ),
                "currency": product.currency,
                "rating": product.rating,
                "reviews": product.reviews,
                "sources": [
                    {
                        "url": source.source_url,
                        "type": source.source_type,
                    }
                    for source in product.sources
                ],
            }
            for product in products
        ]
