from pydantic import BaseModel
from typing import List, Optional
class ProductAnalysis(BaseModel):
    name: Optional[str]
    title: Optional[str]
    asin: Optional[str]
    bullet_points: List[str]
    rating: Optional[float]
    reviews: Optional[int]
    price: Optional[float]
class CompetitorAnalysis(BaseModel):
    target_product: ProductAnalysis
    competitor: ProductAnalysis
    price_difference: Optional[float]