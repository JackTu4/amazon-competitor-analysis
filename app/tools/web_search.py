from app.models.search import SearchResult
from tavily import TavilyClient
from dotenv import load_dotenv
import logging
import os
logger = logging.getLogger(__name__)
load_dotenv()
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)
def search_web(query: str,include_domains: list[str] | None = None):
    logger.info("正在搜索: %s", query)
    try:
        response = tavily_client.search(
            query=query,
            max_results=5,
            include_domains=include_domains,
        )
        results = response.get("results", [])
        if not results:
            return None
        return [
            SearchResult(
            title=result["title"],
            url=result["url"],
            content=result["content"]
        )
            for result in results]
    except Exception as e:
        logger.warning("网页搜索失败: %s", e)
        return None
#def search_web(query:str):
#    print(f"正在搜索:{query}")
#    return {
#       "title":"测试搜索结果",
#       "url":"",
#       "content":""}
#response=search_web("")
#result=SearchResult(**response)