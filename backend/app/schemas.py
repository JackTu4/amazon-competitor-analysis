from pydantic import BaseModel,Field
class AnalysisRequest(BaseModel):
    """商品分析请求参数"""
    target_product: str=Field(
        min_length=1,
        description="需要分析的目标商品名称或 ASIN"
    )
class AnalysisResponse(BaseModel):
    """商品分析任务相应"""
    task_id:str
    status:str
    message:str
    target_product:str