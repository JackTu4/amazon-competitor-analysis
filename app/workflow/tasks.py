from app.tools.web_search import search_web
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
def search_task(query):
    print("执行搜索任务")
    result=search_web(query)
    return result
def read_task(search_result):
    print("执行网页读取任务")
    result=read_webpage(search_result.url)
    return result
def extract_task(data):
    print("执行产品提取任务")
    product=extract_product(
        data["text"],
        data["url"]
    )
    return product