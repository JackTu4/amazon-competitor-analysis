from typing import Optional
from pydantic import BaseModel,Field
class CompetitorCandidate(BaseModel):
    """单个候选竞品的数据结构"""
    product_name:str
    brand:Optional[str]=None
    asin:Optional[str]=None
    product_type:Optional[str]=None
    model: Optional[str] = None
    match_reasons:list[str]=Field(default_factory=list)
    source_url:Optional[str]=None
    # 搜索结果里的原始网页标题，用于 Amazon 详情页被降级时兜底
    source_title:Optional[str]=None
    confidence: float = Field(ge=0, le=1)
    verification_status: str = "待验证"
class CompetitorDiscovery(BaseModel):
    """竞品发现任务的最终结果"""
    target_product:str
    candidates:list[CompetitorCandidate]=Field(default_factory=list)