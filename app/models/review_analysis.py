from pydantic import BaseModel,Field
class ReviewAnalysis(BaseModel):
    """Amazon用户评论分析结果。"""
    total_reviews:int=0
    average_rating:float|None=None
    pain_points:list[str]=Field(default_factory=list)
    positive_aspects:list[str]=Field(default_factory=list)
    improvement_suggestions:list[str]=Field(default_factory=list)
    summary:str=""