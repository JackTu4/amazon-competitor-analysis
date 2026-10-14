import json
from app.agent.competitor_verifier import verify_candidate
from app.agent.prompts import competitor_discovery_prompt
from app.llm.client import client
from app.models.discovery import CompetitorCandidate, CompetitorDiscovery
import os
from dotenv import load_dotenv
load_dotenv()
def extract_competitors(
    target_product: str,
    search_results: list[dict],
) -> CompetitorDiscovery:
    """从搜索网页中提取结构化竞品信息。"""
    if not search_results:
        return CompetitorDiscovery(target_product=target_product)
    # 整理搜索结果，提供给大模型
    search_text = []
    results_by_url = {}
    for index, item in enumerate(search_results, start=1):
        url = item.get("url") or ""
        normalized_url = url.rstrip("/").casefold()
        search_text.append(
            f"搜索结果：{index}\n"
            f"标题：{item.get('title')}\n"
            f"网址：{url}\n"
            f"摘要：{item.get('content')}"
        )
        if normalized_url:
            results_by_url[normalized_url] = item
    # 调用大模型提取候选竞品
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL_NAME", "qwen3.7-flash"),
        messages=[
            {
                "role": "system",
                "content": competitor_discovery_prompt,
            },
            {
                "role": "user",
                "content": (
                    f"目标产品：{target_product}\n\n"
                    + "\n\n".join(search_text)
                ),
            },
        ],
        temperature=0,
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(
            f"竞品提取结果不是有效 JSON：{content}"
        ) from e

    # 校验候选竞品，并转换成数据模型
    extracted_candidates = []

    for item in data.get("candidates", []):
        source_url = item.get("source_url")

        if not source_url:
            print("跳过缺少来源网址的候选商品：", item.get("product_name"))
            continue

        normalized_url = source_url.rstrip("/").casefold()
        matched_result = results_by_url.get(normalized_url)

        if matched_result is None:
            print("跳过来源网址不在搜索结果中的候选商品：", item.get("product_name"))
            continue

        # 检查网页标题和摘要是否能对应候选产品或品牌
        page_title = (matched_result.get("title") or "").casefold()
        page_content = (matched_result.get("content") or "").casefold()
        product_name = (item.get("product_name") or "").casefold()
        brand = (item.get("brand") or "").casefold()

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
                matched_result.get("title"),
            )
            continue

        candidate = CompetitorCandidate(
            product_name=item["product_name"],
            brand=item.get("brand"),
            asin=item.get("asin"),
            model=item.get("model"),
            product_type=item.get("product_type"),
            match_reasons=item.get("match_reasons", []),
            source_url=source_url,
            confidence=item.get("confidence", 0.5),
            verification_status="待验证",
        )

        extracted_candidates.append(candidate)
    # 验证候选竞品
    verified_candidates = [
        verify_candidate(candidate, target_product)
        for candidate in extracted_candidates
    ]

    return CompetitorDiscovery(
        target_product=target_product,
        candidates=verified_candidates,
    )

#workflow 中的discover_task的最终入口
