from pydantic import BaseModel,Field
from typing import Optional
from app.models.extraction import Product, Price
from app.models.review_analysis import ReviewAnalysis

class ProductAnalysis(BaseModel):
    product: Product
    bullet_points: list[str] = Field(default_factory=list)
    rating: Optional[float] = None
    reviews: Optional[int] = None
    price: Optional[Price] = None
    review_analysis: Optional[ReviewAnalysis] = None
class CompetitorAnalysis(BaseModel):
    target_product: ProductAnalysis
    competitor: ProductAnalysis
    price_difference: Optional[float]=None
    summary: Optional[str] = None
class Report(BaseModel):
    title: str
    analysis: CompetitorAnalysis
    summary:Optional[str]=None
