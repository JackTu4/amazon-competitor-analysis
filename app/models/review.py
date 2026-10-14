from pydantic import BaseModel, Field
class Review(BaseModel):
    """单条 Amazon 商品评论的数据结构。"""
    asin: str | None = None
    review_id: str | None = None
    author_name: str | None = None
    rating: float | None = None
    review_header: str | None = None
    review_text: str | None = None
    review_posted_date: str | None = None
    review_country: str | None = None
    helpful_count: str | int | None = None
    is_verified: bool | None = None
    is_amazon_vine: bool | None = None

class ReviewCollection(BaseModel):
    """某个商品的评论集合。"""
    asin: str
    reviews: list[Review] = Field(default_factory=list)
