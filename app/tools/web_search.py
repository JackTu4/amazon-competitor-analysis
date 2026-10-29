from app.models.search import SearchResult
from tavily import TavilyClient
from dotenv import load_dotenv
import logging
import os
from threading import Lock
from copy import deepcopy
logger = logging.getLogger(__name__)
_search_cache = {}
_search_lock = Lock()
load_dotenv()
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)
def search_web(
    query: str,
    include_domains: list[str] | None = None,
    max_results: int = 5,
):
    logger.info("正在搜索: %s", query)

    # 1. 生成缓存键
    domains_key = tuple(sorted(include_domains or []))
    cache_key = (query, domains_key, max_results)

    # 2. 查询缓存
    with _search_lock:
        cached_result = _search_cache.get(cache_key)

    if cached_result is not None:
        logger.info("命中网页搜索缓存: %s", query)
        return deepcopy(cached_result)

    # 3. 缓存未命中，执行原来的搜索
    try:
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            include_domains=include_domains,
        )

        results = response.get("results", [])
        if not results:
            return None

        search_results = [
            SearchResult(
                title=result["title"],
                url=result["url"],
                content=result["content"],
            )
            for result in results
        ]

        # 4. 只缓存成功的搜索结果
        with _search_lock:
            _search_cache[cache_key] = deepcopy(search_results)

        return search_results

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