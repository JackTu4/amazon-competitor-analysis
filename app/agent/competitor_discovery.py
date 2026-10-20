from app.agent.competitor_verifier import extract_capacity
from app.agent.discovery_parser import extract_competitors
from app.tools.web_search import search_web
from concurrent.futures import ThreadPoolExecutor
import time
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
    max_candidates =5
    search_count = 0
    skipped_count = 0
    queries = build_search_queries(target_product)
    search_total_start = time.perf_counter()
    candidates = []
    seen_urls=set()
    target_brand = extract_target_brand(target_product)
    search_total_start = time.perf_counter()

    def search_one(query):
        """执行单条搜索，失败时返回空列表。"""
        try:
            print(f"正在搜索：{query}")
            search_start = time.perf_counter()

            results = search_web(
                query,
                include_domains=["amazon.com"],
            )

            elapsed = time.perf_counter() - search_start
            print(f"搜索完成：{query}，耗时 {elapsed:.2f} 秒")

            return results or []

        except Exception as e:
            print(f"搜索失败：{query}")
            print("错误信息：", e)
            return []

    with ThreadPoolExecutor(max_workers=3) as executor:
        # map 会按照 queries 的原始顺序返回结果
        search_results = list(executor.map(search_one, queries))

    # 第二阶段：严格按照原始 query 顺序处理结果
    for query, results in zip(queries, search_results):
        if len(candidates) >= max_candidates:
            break

        for result in results:
            title = result.title or ""
            url = result.url or ""
            content = result.content or ""

            print("搜索标题：", title)
            print("搜索网址：", url)
            print("搜索摘要：", content[:300] if content else None)
            if not url:
                continue
            search_count += 1

            # 优先保留 Amazon 商品详情页
            if "/dp/" not in url and "/gp/product/" not in url:
                print("跳过非商品详情页：", url)
                skipped_count += 1
                continue

            target_capacity = extract_capacity(target_product)
            title_capacity = extract_capacity(title)

            if (
                    target_capacity
                    and title_capacity
                    and target_capacity != title_capacity
            ):
                print("跳过容量不匹配的商品：", title)
                skipped_count += 1
                continue

            if target_brand and target_brand in title.casefold():
                skipped_count += 1
                print("跳过目标品牌自己的网页：", title)
                continue

            normalized_url = url.rstrip("/").casefold()

            if normalized_url in seen_urls:
                print("跳过重复 URL：", url)
                continue
            seen_urls.add(normalized_url)
            candidates.append({
                "search_query": query,
                "title": title,
                "url": url,
                "content": content,
            })
            if len(candidates) >= max_candidates:
                break
    print("搜索结果数量：", search_count)
    print("跳过的页面数量：", skipped_count)
    print("最终保留的页面数量：", len(candidates))
    print(
        f"候选网页搜索总耗时："
        f"{time.perf_counter() - search_total_start:.2f} 秒"
    )
    return candidates   #获得了一个具有search_query、title、url、content的candidates列表
def run_discovery(target_product: str):
    """执行竞品发现的完整流程，并统计各阶段耗时。"""
    total_start = time.perf_counter()

    # 第一步：搜索候选网页
    search_start = time.perf_counter()
    search_results = discover_candidates(target_product)
    search_elapsed = time.perf_counter() - search_start

    # 第二步：提取并验证竞品
    extract_start = time.perf_counter()
    result = extract_competitors(
        target_product,
        search_results,
    )
    extract_elapsed = time.perf_counter() - extract_start
    total_elapsed = time.perf_counter() - total_start
    print("\n========== 竞品发现耗时统计 ==========")
    print(f"候选网页搜索耗时：{search_elapsed:.2f} 秒")
    print(f"提取与验证总耗时：{extract_elapsed:.2f} 秒")
    print(f"竞品发现总耗时：{total_elapsed:.2f} 秒")
    return result


if __name__ == "__main__":
    target_product = input("请输入目标产品：")
    result = run_discovery(target_product)
    print("\n========== 竞品发现结果 ==========")
    print(result.model_dump_json(indent=2))

