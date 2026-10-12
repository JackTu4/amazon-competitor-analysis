from app.models.discovery import CompetitorCandidate
from app.tools.web_search import search_web
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
import re
from urllib.parse import urlparse
from app.agent.verification_status import verify_product_specs

def extract_capacity(text: str) -> str | None:
    m = re.search(r"(\d+)\s*(?:gb|tb)", text or "", re.IGNORECASE)
    return m.group(1) if m else None

def extract_asin(url: str) -> str | None:
    """从亚马逊商品 URL 中提取 ASIN。"""
    if not url:
        return None
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    # 只接受常见的亚马逊国家站点域名
    amazon_domain = re.search(
        r"(?:^|\.)amazon\.(?:com|co\.uk|co\.jp|de|fr|it|es|ca|com\.au|in|com\.mx|com\.br|nl|sg|ae|sa|se|pl|com\.tr)$",
        hostname,
    )
    if not amazon_domain:
        return None
    match = re.search(
        r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?#]|$)",
        parsed.path,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).upper()
    return None

def verify_candidate(candidate: CompetitorCandidate,target_product: str,) -> CompetitorCandidate:
    """为单个候选竞品搜索独立的产品详情页。"""
    query = (
        f'{candidate.brand or ""} '
        f'{candidate.product_name} '
        f'{candidate.model or ""} '
        f'256GB NVMe SSD product page'
    ).strip()
    print(f"正在验证候选竞品：{candidate.product_name}")
    print(f"验证搜索词：{query}")
    try:
        results = search_web(query,include_domains=["amazon.com"])
    except Exception as e:
        print("候选竞品搜索失败：", e)
        return candidate
    if not results:
        print("没有找到候选竞品的独立详情页")
        return candidate
    results = results if isinstance(results, list) else [results]
    target_brand = (candidate.brand or "").casefold()
    target_name = candidate.product_name.casefold()
    target_model = (candidate.model or "").casefold()
    target_capacity = extract_capacity(target_product)
    page_read_success = False
    product_info = None
    initial_asin = candidate.asin
    initial_source_url = candidate.source_url
    for result in results:
        title = (result.title or "").casefold()
        url = result.url or ""
        asin = extract_asin(url)
        if not asin:
            print("跳过非亚马逊商品详情页：", url)
            continue
        brand_matches = bool(target_brand and target_brand in title)
        name_matches = target_name in title
        model_matches = bool(target_model and target_model in title)
        if not (brand_matches or name_matches or model_matches):
            continue
        if "huadisk" in title:
            continue
        if target_capacity:
            title_capacity = extract_capacity(title)
            if title_capacity and title_capacity != target_capacity:
                print("容量不匹配，跳过：", result.title)
                continue
        print("找到候选详情页：", result.title)
        print("详情页网址：", url)
        try:
            page = read_webpage(url)
            if not page or not page.get("text"):
                print("网页正文为空，尝试下一个搜索结果")
                continue
            extracted = extract_product(
                page["text"],
                page["url"],
                result.title
            )
        except Exception as e:
            print("读取或提取商品信息失败：", e)
            fallback_asin = extract_asin(url)
            if fallback_asin:
                candidate.asin = fallback_asin
                candidate.source_url = url
                break
            continue
        product = extracted.product
        product_info = product.model_dump()
        print("提取到的商品名称：", product.name)
        print("提取到的商品标题：", product.title)
        print("提取到的 ASIN：", product.asin)
        candidate.source_url = page["url"]
        page_asin = extract_asin(page.get("url") or url)
        if not page_asin:
            print("最终网页网址无法提取 ASIN，继续搜索下一个结果")
            continue
        candidate.asin = page_asin
        page_read_success = True
        spec_result = verify_product_specs(
            page_text=page["text"],
            product_info=product_info,)
        candidate.verification_status = spec_result["verification_status"]
        print("参数核验结果：", spec_result)
        break
    print("从 URL 解析出的 ASIN：", candidate.asin)
    if page_read_success:
        pass
    else:
        # 验证失败时，恢复初始搜索结果中的 ASIN 和 URL
        if not candidate.asin:
            candidate.asin = initial_asin

        if not candidate.source_url:
            candidate.source_url = initial_source_url

        if candidate.asin:
            candidate.verification_status = "仅提取ASIN"
        else:
            candidate.verification_status = "验证失败，未获取有效详情页"

    return candidate
