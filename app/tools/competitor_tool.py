from app.agent.competitor_discovery import run_discovery
def discover_competitors_tool(target_product:str)->dict:
    """自动搜索、筛选并验证目标产品的竞品"""
    result = run_discovery(target_product)
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result

"""将竞品自动分析中的几个业务逻辑 包括discover ，parser，verifier包装成 discover_competitors_tool
工具  python选择是否调用这个工具 决定好了之后再pyhon在进行调用 """