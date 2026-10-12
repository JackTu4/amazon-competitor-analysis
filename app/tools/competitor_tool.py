from app.agent.competitor_discovery import run_discovery
def discover_competitors_tool(target_product:str)->dict:
    """自动搜索、筛选并验证目标产品的竞品"""
    result = run_discovery(target_product)
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result