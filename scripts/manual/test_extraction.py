import sys
from pathlib import Path

# 允许直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.extraction import (ProductExtraction,
    Price,Product,Feature,Source )
data = ProductExtraction(
    product=Product(
        name="Samsung SSD",
        title="Samsung SSD 870 EVO 1TB",
        asin="B08QBJ2YMG",
        brand="Samsung",
    ),
    price=Price(
        amount=99.99,
        currency="USD",
    ),
    features=[
        Feature(
            name="Read Speed",
            description="Up to 560MB/s",
        ),
        Feature(
            name="Capacity",
            description="1TB",
        ),
    ],
    source=Source(
        title="Samsung SSD 870 EVO",
        url="https://example.com",
    ),
)


print(data)