from app.models.discovery import CompetitorCandidate
from app.tools.web_search import search_web
from app.tools.web_reader import read_webpage
from app.agent.extractor import extract_product
import re
def extract_asin(url: str) -> str | None:
    """从亚马逊商品 URL 中提取 ASIN。"""
    if not url:
        return None
    match = re.search(
        r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?#]|$)",
        url,
        re.IGNORECASE
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
        results = search_web(query)
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
    for result in results:
        title = (result.title or "").casefold()
        url = result.url or ""
        brand_matches = bool(target_brand and target_brand in title)
        name_matches = target_name in title
        model_matches = bool(target_model and target_model in title)
        if not (brand_matches or name_matches or model_matches):
            continue
        if "huadisk" in title:
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
            continue
        product = extracted.product
        print("提取到的商品名称：", product.name)
        print("提取到的商品标题：", product.title)
        print("提取到的 ASIN：", product.asin)
        candidate.source_url = page["url"]
        print("从 URL 解析出的 ASIN：", candidate.asin)
        candidate.verification_status = "详情页已读取，参数待核验"
        return candidate
    print("没有找到标题匹配的独立详情页")
    return candidate
