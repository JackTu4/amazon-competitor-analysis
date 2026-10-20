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


def find_target_asin(target_product: str) -> dict | None:
    """搜索目标商品，并初步校验 Amazon 商品标题。"""
    query = f"{target_product} site:amazon.com product"

    results = search_web(
        query,
        include_domains=["amazon.com"],
    )

    if not results:
        print("没有搜索到目标商品网页")
        return None

    # 兼容搜索工具返回列表或单个结果
    results = results if isinstance(results, list) else [results]

    # 从目标商品描述中提取品牌和容量线索
    target_text = target_product.casefold()
    target_capacity = extract_capacity(target_product)

    for result in results:
        title = result.title or ""
        url = result.url or ""
        asin = extract_asin(url)

        if not asin:
            continue

        title_lower = title.casefold()

        # 如果目标商品指定了容量，而标题中也出现容量，
        # 则两者不一致时跳过。
        title_capacity = extract_capacity(title)
        if (
            target_capacity
            and title_capacity
            and target_capacity != title_capacity
        ):
            print("目标商品容量不匹配，跳过：", title)
            continue

        print("候选目标商品：", title)
        print("商品链接：", url)
        print("提取到的 ASIN：", asin)

        # 返回候选结果，供后续检查
        return {
            "asin": asin,
            "title": title,
            "url": url,
        }
    print("没有找到符合基本条件的 Amazon 商品详情页")
    return None

def is_candidate_url_match(candidate, url: str) -> bool:
    """初步判断 Amazon URL 是否与候选商品匹配。"""
    if not url:
        return False

    asin = extract_asin(url)
    if not asin:
        return False

    # 如果候选对象已有 ASIN，必须与 URL 中的 ASIN 一致
    if candidate.asin and candidate.asin.upper() != asin:
        return False

    return True
def verify_candidate(candidate: CompetitorCandidate,target_product: str,) -> CompetitorCandidate:
    """为单个候选竞品搜索独立的产品详情页。"""
    existing_url = candidate.source_url or ""
    existing_asin = extract_asin(existing_url)

    # 只有候选 ASIN 与 URL ASIN 一致时，才允许直接复用
    can_reuse_url = (
            bool(existing_asin)
            and bool(candidate.asin)
            and candidate.asin.upper() == existing_asin
    )

    if can_reuse_url:
        print("复用已有 Amazon 详情页：", existing_url)
        results = [
            {
                "title": candidate.product_name or "",
                "url": existing_url,
            }
        ]
    else:
        query = (
            f'{candidate.brand or ""} '
            f'{candidate.product_name or ""} '
            f'{candidate.model or ""} '
            f'Amazon product page'
        ).strip()

        print(f"正在验证候选竞品：{candidate.product_name}")
        print(f"验证搜索词：{query}")

        try:
            results = search_web(
                query,
                include_domains=["amazon.com"],
            )
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
    candidate_capacity = extract_capacity(
        f"{candidate.product_name or ''} {candidate.model or ''}"
    )
    page_read_success = False
    product_info = None
    initial_asin = candidate.asin
    initial_source_url = candidate.source_url
    for result in results:
        if isinstance(result, dict):
            result_title = result.get("title") or ""
            url = result.get("url") or ""
        else:
            result_title = result.title or ""
            url = result.url or ""
        title = result_title.casefold()
        asin = extract_asin(url)
        if not asin:
            print("跳过非亚马逊商品详情页：", url)
            continue
        brand_matches = bool(
            target_brand and target_brand in title
        )
        name_matches = bool(
            target_name and target_name in title
        )
        model_matches = bool(
            target_model and target_model in title
        )
        is_existing_url = (
                url.rstrip("/").casefold()
                == existing_url.rstrip("/").casefold()
        )

        if not (
                brand_matches or name_matches or model_matches
        ):
            print("商品标题匹配度不足，跳过：", url)
            continue
        if "huadisk" in title:
            continue
        if candidate_capacity:
            title_capacity = extract_capacity(title)
            if title_capacity and title_capacity != candidate_capacity:
                print("竞品容量不匹配，跳过：", url)
                continue
        print("找到候选详情页：", result_title)
        print("详情页网址：", url)
        try:
            page = read_webpage(url)
            if not page or not page.get("text"):
                print("网页正文为空，尝试下一个搜索结果")
                continue
            extracted = extract_product(
                page["text"],
                page["url"],
                result_title
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
        extracted_title = (
                product.title or product.name or ""
        ).casefold()

        if target_name not in extracted_title and (
                not target_brand or target_brand not in extracted_title
        ):
            print(
                "详情页内容与候选商品不一致，跳过：",
                url,
                "| 页面标题 =", product.title,
                "| 候选商品 =", candidate.product_name,
            )
            continue
        product_info = product.model_dump()

        print("提取到的商品名称：", product.name)
        print("提取到的商品标题：", product.title)
        print("提取到的 ASIN：", product.asin)

        page_url = page.get("url") or url
        page_asin = extract_asin(page_url)
        extracted_asin = (product.asin or "").strip().upper()
        if not page_asin:
            print("最终网页网址无法提取 ASIN，继续搜索下一个结果")
            continue
        # 网页提取出的 ASIN 与 URL 中的 ASIN 不一致时，不直接认定商品核验成功
        if extracted_asin and extracted_asin != page_asin:
            print(
                "ASIN 不一致，跳过该页面：",
                "网页提取 ASIN =", extracted_asin,
                "| URL ASIN =", page_asin,
            )
            continue
        candidate.source_url = page_url
        candidate.asin = page_asin
        page_read_success = True
        try:
            spec_result = verify_product_specs(
                page_text=page["text"],
                product_info=product_info,
            )

            verification_status = spec_result.get(
                "verification_status",
                "参数核验结果未知",
            )
            candidate.verification_status = verification_status
            print("参数核验结果：", spec_result)
            # 只有参数核验函数正常返回，才结束当前候选的验证
            page_read_success = True
            break
        except Exception as e:
            print("商品参数核验失败：", e)
            candidate.verification_status = "参数核验失败"
            continue
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
