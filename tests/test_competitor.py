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
print("====================")
print("对象输出")
print(analysis)
print("====================")
print("字典输出")
data=analysis.model_dump()
print(data)
print("====================")
print("JSON输出")
json_data = analysis.model_dump_json(
    indent=2
)
print(json_data)