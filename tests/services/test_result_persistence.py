"""商品明细落库的集成测试：需要本地 MySQL 与 .env 配置。"""

from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.competitor import (
    CompetitorAnalysis,
    ProductAnalysis,
)
from app.models.extraction import Price, Product
from app.workflow.result import WorkflowResult

from backend.app.db.crud.product import delete_products_by_task
from backend.app.db.database import SessionLocal
from backend.app.db.models import Project, ReportRecord
from backend.app.services.analysis_service import run_analysis
from backend.app.services.result_service import (
    get_analysis_products,
    save_analysis_results,
)
from backend.app.services.task_service import create_task_record

pytestmark = pytest.mark.integration


def make_product(name, asin, rating):
    return ProductAnalysis(
        product=Product(
            name=name,
            title=f"{name} 产品标题",
            asin=asin,
            brand=name.split()[0],
        ),
        bullet_points=["高速读写"],
        rating=rating,
        reviews=10,
        price=Price(amount=49.99, currency="USD"),
    )


def test_save_analysis_results_persists_products_and_sources():
    task_id = str(uuid4())

    create_task_record(
        task_id=task_id,
        target_product="HUADISK SSD",
    )

    target = make_product("HUADISK SSD", "B0TARGET01", 4.5)
    competitor_a = make_product("Samsung SSD", "B0COMPA001", 4.7)
    competitor_b = make_product("Kingston SSD", "B0COMPB001", 4.6)

    result = WorkflowResult(
        report_path="reports/fake.md",
        target_product="HUADISK SSD",
        task_id=task_id,
        target_asin="B0TARGET01",
        analyses=[
            {
                "competitor_name": "Samsung SSD",
                "competitor_asin": "B0COMPA001",
                "competitor_url": "https://www.amazon.com/dp/B0COMPA001",
                "analysis": CompetitorAnalysis(
                    target_product=target,
                    competitor=competitor_a,
                ),
            },
            {
                "competitor_name": "Kingston SSD",
                "competitor_asin": "B0COMPB001",
                "competitor_url": None,
                "analysis": CompetitorAnalysis(
                    target_product=target,
                    competitor=competitor_b,
                ),
            },
            {
                "competitor_name": "坏竞品",
                "analysis": {"error": "timeout"},
            },
        ],
        failures=[{"competitor_name": "坏竞品", "reason": "timeout"}],
    )

    try:
        count = save_analysis_results(task_id, result)

        # 1 个目标商品 + 2 个竞品
        assert count == 3

        products = get_analysis_products(task_id)

        assert [p["role"] for p in products].count("target") == 1
        assert [p["role"] for p in products].count("competitor") == 2

        target_row = next(p for p in products if p["role"] == "target")
        assert target_row["asin"] == "B0TARGET01"
        assert target_row["price"] == 49.99
        assert target_row["sources"][0]["url"].endswith("/B0TARGET01")

        competitor_row = next(
            p for p in products if p["asin"] == "B0COMPA001"
        )
        assert competitor_row["name"] == "Samsung SSD"
        assert competitor_row["rating"] == 4.7
        assert competitor_row["sources"][0]["type"] == "amazon"

        # 失败竞品不落库
        assert all(p["asin"] != "坏竞品" for p in products)

        # 重复执行应保持幂等，不产生重复行
        save_analysis_results(task_id, result)
        assert len(get_analysis_products(task_id)) == 3

    finally:
        with SessionLocal() as db:
            delete_products_by_task(db, task_id)

            project = db.get(Project, task_id)

            if project is not None:
                db.delete(project)

            db.commit()


def test_run_analysis_persists_products_end_to_end(tmp_path, monkeypatch):
    """工作流产出 -> 明细落库 -> 报告与任务完成，全链路跑通。"""

    monkeypatch.chdir(tmp_path)

    task_id = str(uuid4())
    target_product = "HUADISK SSD"

    create_task_record(
        task_id=task_id,
        target_product=target_product,
    )

    target = make_product("HUADISK SSD", "B0TARGET01", 4.5)
    competitor = make_product("Samsung SSD", "B0COMPA001", 4.7)

    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    report_path = report_dir / f"{task_id}.md"
    report_path.write_text(
        "# 亚马逊竞品分析报告\n\n测试报告",
        encoding="utf-8",
    )

    workflow_result = WorkflowResult(
        report_path=report_path,
        target_product=target_product,
        task_id=task_id,
        target_asin="B0TARGET01",
        analyses=[
            {
                "competitor_name": "Samsung SSD",
                "competitor_asin": "B0COMPA001",
                "competitor_url": "https://www.amazon.com/dp/B0COMPA001",
                "analysis": CompetitorAnalysis(
                    target_product=target,
                    competitor=competitor,
                ),
            },
        ],
    )

    try:
        # 用假的 execute_workflow 替换真实 Agent 调用
        with patch(
            "backend.app.services.analysis_service.execute_workflow",
            return_value=workflow_result,
        ):
            run_analysis(task_id, target_product)

        # 1. 商品明细已落库
        products = get_analysis_products(task_id)
        assert len(products) == 2
        assert {p["role"] for p in products} == {"target", "competitor"}

        # 2. 任务完成、报告落库
        with SessionLocal() as db:
            project = db.get(Project, task_id)

            assert project is not None
            assert project.status == "completed"
            assert project.result == str(report_path)

            report = (
                db.query(ReportRecord)
                .filter(ReportRecord.task_id == task_id)
                .first()
            )

            assert report is not None
            assert "测试报告" in report.markdown

    finally:
        with SessionLocal() as db:
            delete_products_by_task(db, task_id)

            report = (
                db.query(ReportRecord)
                .filter(ReportRecord.task_id == task_id)
                .first()
            )

            if report is not None:
                db.delete(report)

            project = db.get(Project, task_id)

            if project is not None:
                db.delete(project)

            db.commit()
