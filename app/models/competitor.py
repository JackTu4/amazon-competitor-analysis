from pydantic import BaseModel
from typing import List, Optional
from app.models.extraction import Product
class Price(BaseModel):
    amount: Optional[float]=None
    currency: Optional[str]=None
class ProductAnalysis(BaseModel):
    product: Product
    bullet_points: list[str] = []
    rating: Optional[float] = None
    reviews: Optional[int] = None
    price: Optional[Price] = None
class CompetitorAnalysis(BaseModel):
    target_product: ProductAnalysis
    competitor: ProductAnalysis
    price_difference: Optional[float]=None
class Report(BaseModel):
    title: str
    analysis: CompetitorAnalysis
    summary:Optional[str]=None
