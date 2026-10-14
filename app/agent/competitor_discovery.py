from app.agent.discovery_parser import extract_competitors
from app.tools.web_search import search_web

def build_search_queries(target_product: str) -> list[str]:
    """生成更适合寻找不同品牌竞品的搜索词。"""
    parts = target_product.strip().split()
    # 第一个单词是目标品牌，去掉它
    spec = " ".join(parts[1:]) if len(parts) > 1 else target_product
    return [
        f"{spec} alternatives other brands",
        f"best {spec}",
        f"similar products to {spec}",
    ]
def extract_target_brand(target_product:str) -> str|None:
    """从当前输入的目标产品名称中提取品牌。"""
    parts=target_product.strip().split()   #按照产品名称进行切分成单词列表  切分以后第一个单词就是品牌名
    if not parts:
        return None
    return parts[0].casefold()  #`casefold()`转为小写
def discover_candidates(target_product:str)->list[dict]:
    """搜索目标产品的潜在竞品,并按url去重"""
    search_count = 0
    skipped_count = 0
    queries= build_search_queries(target_product)
    candidates=[]
    seen_urls=set()
    target_brand = extract_target_brand(target_product)
    for query in queries:
        try:
            print(f"正在搜索:{query}")
            results=search_web(query, include_domains=["amazon.com"])
            if not results:
                continue
            for result in results:
                title = result.title
                url = result.url
                content = result.content
                print("搜索标题：", title)
                print("搜索网址：", url)
                print("搜索摘要：", content[:300] if content else None)
                if not url:
                    continue
                search_count += 1
                if target_brand and target_brand in title.casefold():
                    skipped_count += 1
                    print("跳过目标品牌自己的网页：", title)
                    continue
                normalized_url = url.rstrip("/").casefold()  #目的：`https://ABC.COM/` 和 `https://abc.com` 识别成同一个链接。
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)
                candidates.append({
                    "search_query":query,
                    "title":title,
                    "url":url,
                    "content":content,
                })
        except Exception as e:
            print(f"搜索失败:{query}")
            print("错误信息",e)
    print("搜索结果数量：", search_count)
    print("跳过的页面数量：", skipped_count)
    print("最终保留的页面数量：", len(candidates))
    return candidates   #获得了一个具有search_query、title、url、content的candidates列表
def run_discovery(target_product: str):
    """执行竞品发现的完整流程。"""
    # 第一步：搜索候选网页
    search_results = discover_candidates(target_product)
    # 第二步：提取并验证竞品
    result = extract_competitors(
        target_product,
        search_results,
    )
    return result


if __name__ == "__main__":
    target_product = input("请输入目标产品：")
    result = run_discovery(target_product)
    print("\n========== 竞品发现结果 ==========")
    print(result.model_dump_json(indent=2))

