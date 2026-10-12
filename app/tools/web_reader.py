import requests
import time
from bs4 import BeautifulSoup
def cleantext(text:str):
    lines=[]
    for line in text.splitlines():  #把空行变成""
        line=line.strip()
        if line:
            lines.append(line)
    return "\n".join(lines)
def read_webpage(url:str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.amazon.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    response = None
    last_err = None
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                raise Exception(f"网页请求失败:{response.status_code}")
            response.raise_for_status()
            break
        except Exception as e:
            last_err = e
            response = None
            time.sleep(2 * (attempt + 1))
    if response is None:
        raise last_err
    soup = BeautifulSoup(response.content, "html.parser")
    for tag in soup.select(
            "script, style, noscript, svg, "
            "header, footer, nav, iframe"
    ):
        tag.decompose()
    lines=[]
    seen=set()
    ignore_phrases=[
        "Add to cart",
        "Buy Now",
        "Add to List",
        "Added to",
        "Select delivery location",
        "Sign in to continue",
        "FREE Returns",
        "Return this item for free",
        "Read full return policy",
        "Learn more",
        "See more",
        "Report an issue with this product or seller",
        "Customers also viewed these products",
        "Previous set of slides",
        "Start over",
        "Image Unavailable",
        "Image not available for",
        "VIDEOS",
        "360° VIEW",
        "IMAGES",
        "Gift options",
        "Secure transaction",
        "Product support included",
        "To see product details, add this item to your cart.",
        "Brief content visible, double tap to read full content.",
        "Full content visible, double tap to read brief content.",
        "Sorry, there was a problem.",
        "List unavailable.",
        "Get it as soon as",
        "FREE Shipping by Amazon",
        "No Import Charges",
        "Shipping & Fee Details",
        "AmazonGlobal Shipping",
        "Estimated Import Charges",
        "Sales taxes may apply at checkout",
        "Shipping cost, delivery date",
        "Deliver to",
        "delivery",
        "Quantity:",
        "Subtotal",
        "Initial payment breakdown",
        "Includes selected options",
        "Includes initial monthly payment",
        "Purchase options and add-ons",

        # 卖家、退货和支付说明
        "Ships from",
        "Sold by",
        "30-day refund",
        "Quick refund",
        "Usually issued within",
        "Shipping fee",
        "Convenient dropoff",
        "See exceptions",
        "See details",
        "Your transaction is secure",
        "We work hard to protect your security and privacy",
        "This item is a gift",
        "Available at checkout",
        "Unable to add item to List",
        "error retrieving your Wish Lists",

        # Amazon 推荐商品区域
        "Consider a similar item",
        "Featured items to consider",
        "Amazon's Choice",
        "Customers also viewed",
        "Featured items",
        # Amazon 内部数据
        "desktop_buybox_group",
        "offerListingId",
        "buyingOptionType",
        "symbolPosition",
        "fractionalValue",
        "integerValue",

        # 价格 / 配送 / 库存 / 支付
        "FREE Shipping",
        "In Stock",
        "FREE Returns",
        "See return policy",
        "At any of our",
        "What's Product Support",
        "At checkout, you can add",

        # 购买框 / 数量选择 / 增强选项
        "Enhancements you chose",
        "To add the following enhancements",
        "choose a different seller",
        "not available for the seller",
        "unavailable for quantities",
        "cardName",
        "Make a ",
        "See 0 options",

        # 组合购买 / 相关商品
        "Frequently bought together",
        "Add both to Cart",
        "Choose items to buy together",
        "To see our price, add these items",
        "Try again!",
        "Total price",
        "List Price",
        "List:",
        "Show details",
        "Hide details",
        "fractionalValue",
        "integerValue",
        ]
    import re
    def remove_amazon_json(text: str) -> str:
        text = re.sub(
            r'\{"desktop_buybox_group_1".*?\}\]',
            '',
            text,
            flags=re.DOTALL
        )
        return text

    for line in soup.stripped_strings:
        line = " ".join(line.split())
        if not line:
            continue
        # 过滤无关提示语
        if any(
                phrase.lower() in line.lower()
                for phrase in ignore_phrases
        ):
            continue
        # 过滤单独出现的价格符号、货币代码和分隔符
        if line in {"S$", "$", "S", ".", "£", "€", "›", "TWD"}:
            continue
        # 过滤被拆分的价格/评分/数量数字，如 "1,611"、"94"、"1 2 3 4 5"
        if re.fullmatch(r"[\d\s\.,]+", line):
            continue
        # 过滤配送日期行，如 "Tuesday, October 27" / "Friday, Oct 23"
        if re.fullmatch(
            r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
            r"January|February|March|April|June|July|August|September|"
            r"October|November|December)\.?\s+\d{1,2}",
            line,
        ):
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = remove_amazon_json(text)
    return {
        "url": url,
        "text": text
    }
