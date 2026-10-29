import sys
from pathlib import Path

# 允许直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.competitor import CompetitorAnalysis, ProductAnalysis,Price
from app.models.extraction import Product
target = ProductAnalysis(
    product=Product(
        name="HUADISK SSD",
        title="HUADISK NVMe SSD",
        asin="B001",
        brand="HUADISK"
    ),
    bullet_points=[
        "High speed",
        "NVMe SSD"
    ],
    rating=4.5,
    reviews=200,
    price=Price(
        amount=50,
        currency="USD"
))
competitor = ProductAnalysis(
    product=Product(
        name="Samsung SSD",
        title="Samsung 980 SSD",
        asin="B002",
        brand="Samsung"
    ),
    bullet_points=[
        "High performance",
        "Reliable"
    ],
    rating=4.8,
    reviews=5000,
    price=Price(
        amount=70,
        currency="USD"
    )
)
analysis = CompetitorAnalysis(
    target_product=target,
    competitor=competitor,
    price_difference=competitor.price.amount -
        target.price.amount
)

