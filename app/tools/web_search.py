from app.models.search import SearchResult
from tavily import TavilyClient
import os
tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)
def search_web(query: str):
    print(f"正在搜索:{query}")
    response = tavily_client.search(
        query=query,
        max_results=1
    )
    result = response["results"][0]
    return SearchResult(
        title=result["title"],
        url=result["url"],
        content=result["content"]
    )
#def search_web(query:str):
#    print(f"正在搜索:{query}")
#    return {
#       "title":"测试搜索结果",
#       "url":"",
#       "content":""}
#response=search_web("")
#result=SearchResult(**response)