from app.models.discovery import (CompetitorCandidate,CompetitorDiscovery,)
from app.tools.web_search import search_web
import json
from app.llm.client import client
from app.agent.prompts import competitor_discovery_prompt
from app.agent.competitor_verifier import verify_candidate
def build_search_queries(target_product: str) -> list[str]:
    """生成更适合寻找不同品牌竞品的搜索词。"""
    return [
        f"{target_product} alternatives other brands",
        f"best competing brands for {target_product}",
        f"similar products to {target_product}",
    ]
def extract_target_brand(target_product:str) -> str|None:
    """从当前输入的目标产品名称中提取品牌。"""
    parts=target_product.strip().split()   #按照产品名称进行切分成单词列表  切分以后第一个单词就是品牌名
    if not parts:
        return None
    return parts[0].casefold()  #`casefold()`转为小写
def discover_candidates(target_product:str)->list[dict]:
    """搜索目标产品的潜在竞品,并按url去重"""
    queries= build_search_queries(target_product)
    candidates=[]
    seen_urls=set()
    target_brand = extract_target_brand(target_product)
    for query in queries:
        try:
            print(f"正在搜索:{query}")
            result=search_web(query)
            if not result:
                continue
            title=result.title
            url=result.url
            content=result.content
            print("搜索标题：", title)
            print("搜索网址：", url)
            print("搜索摘要：", content[:300] if content else None)
            if not url:
                continue
            if target_brand and target_brand in title.casefold():
                print("跳过目标品牌自己的网页：", title)
                continue
            normalized_url=url.rstrip("/").lower()  #目的：`https://ABC.COM/` 和 `https://abc.com` 识别成同一个链接。
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
    return candidates
def extract_competitors(
        target_product:str,
        search_results:list[dict],
)->CompetitorDiscovery:
    """从搜索网页中提取结构化竞品信息"""
    if not search_results:
        return CompetitorDiscovery(
            target_product=target_product,
        )
    search_text=[]
    for index,item in enumerate(search_results,start=1):
        search_text.append(f"""
搜索结果:{index}
标题:{item.get("title")}
网址:{item.get("url")}
摘要:{item.get("content")}""")
    response = client.chat.completions.create(
        model="qwen3.7-flash",
        messages=[
            {
                "role": "system",
                "content": competitor_discovery_prompt,
            },
            {
                "role": "user",
                "content": (
                         f"目标产品：{target_product}\n\n"
                          + "\n".join(search_text)
                ),
            },
        ],
        temperature=0,
    )
    content=response.choices[0].message.content
    try:
        data=json.loads(content)
    except(json.JSONDecodeError,TypeError) as e:
        raise ValueError(
            f"竞品提取结果不是有效 JSON:{content}"
        ) from e
    valid_urls={
        item["url"].rstrip("/")
        for item in search_results
        if item.get("url")
    }
    extracted_candidates=[]
    for item in data.get("candidates", []):
        source_url = item.get("source_url")
        # 只接受本次搜索结果中实际存在的网址
        if not source_url:
            print("跳过缺少来源网址的候选商品：", item.get("product_name"))
            continue
        if source_url.rstrip("/") not in valid_urls:
            print("跳过来源网址不在搜索结果中的候选商品：", item.get("product_name"))
            continue
        normalized_source_url = source_url.rstrip("/").casefold()
        normalized_valid_urls = {
            url.rstrip("/").casefold()
            for url in valid_urls
        }
        if normalized_source_url not in normalized_valid_urls:
            print(
                "跳过来源网址不在搜索结果中的候选商品：",
                item.get("product_name")
            )
            continue

        # 检查来源网页标题是否能对应候选品牌或产品名称
        matched_result = next(
            (
                result for result in search_results
                if result.get("url", "").rstrip("/").casefold()
                   == normalized_source_url
            ),
            None
        )
        if matched_result is None:
            continue
        page_title = matched_result.get("title", "").casefold()
        page_content = matched_result.get("content", "").casefold()
        product_name = item.get("product_name", "").casefold()
        brand = (item.get("brand") or "").casefold()
        # 标题或摘要中至少有一个能够匹配候选产品
        if (
                product_name not in page_title
                and product_name not in page_content
                and (
                not brand
                or (
                        brand not in page_title
                        and brand not in page_content
                )
        )
        ):
            print(
                "跳过标题和摘要均不匹配的候选商品：",
                item.get("product_name"),
                "| 网页标题：",
                matched_result.get("title")
            )
            continue
        candidate = CompetitorCandidate(
            product_name=item["product_name"],
            brand=item.get("brand"),
            asin=item.get("asin"),
            model=item.get("model"),
            product_type=item.get("product_type"),
            match_reasons=item.get("match_reasons", []),
            source_url=item.get("source_url"),
            confidence=item.get("confidence", 0.5),
            verification_status="待验证",
        )
        extracted_candidates.append(candidate)
    verified_candidates = [
        verify_candidate(candidate, target_product)
        for candidate in extracted_candidates
    ]
    return CompetitorDiscovery(
        target_product=target_product,
        candidates=verified_candidates,
    )
if __name__ == "__main__":
    target_product = input("请输入目标产品：")
    # 第一步：搜索候选网页
    search_results = discover_candidates(target_product)

    print("\n========== 候选网页 ==========")
    for item in search_results:
        print("标题：", item["title"])
        print("网址：", item["url"])

    # 第二步：从网页中提取竞品
    result = extract_competitors(
        target_product,
        search_results,
    )
    print("\n========== 提取出的竞品 ==========")
    print(result.model_dump_json(indent=2))
