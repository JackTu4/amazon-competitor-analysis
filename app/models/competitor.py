from pydantic import BaseModel,Field
from typing import List, Optional
from app.models.extraction import Product
class Price(BaseModel):
    amount: Optional[float]=None
    currency: Optional[str]=None
class ProductAnalysis(BaseModel):
    product: Product
    bullet_points: list[str] = Field(default_factory=list)
    rating: Optional[float] = None
    reviews: Optional[int] = None
    price: Optional[Price] = None
class CompetitorAnalysis(BaseModel):
    target_product: ProductAnalysis
    competitor: ProductAnalysis
    price_difference: Optional[float]=None
    summary: Optional[str] = None
class Report(BaseModel):
    title: str
    analysis: CompetitorAnalysis
    summary:Optional[str]=None
