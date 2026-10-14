from typing import Optional
from pydantic import BaseModel,Field


class Source(BaseModel):
    url: str
    title: Optional[str] = None
class Product(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    asin: Optional[str] = None
    brand: Optional[str] = None
    capacity: Optional[str] = None
    interface: Optional[str] = None
    form_factor: Optional[str] = None
    model: Optional[str] = None
class Price(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
class Feature(BaseModel):
    name: str
    description: str
class ProductExtraction(BaseModel):
    product: Product
    price: Price
    features: list[Feature] = Field(default_factory=list)
    source: Source
    rating: Optional[float] = None
    reviews: Optional[int] = None
    bullet_points: list[str] = Field(default_factory=list)