from app.models.extraction import Price
def analyze_price(
    target_price: Price | None,
    competitor_price: Price | None,
) -> dict:
    """分析目标商品与竞品之间的价格差异。"""
    if (
        target_price is None
        or competitor_price is None
        or target_price.amount is None
        or competitor_price.amount is None
    ):
        return {
            "target_price": target_price.amount if target_price else None,
            "competitor_price": (
                competitor_price.amount if competitor_price else None
            ),
            "price_difference": None,
            "price_difference_percent": None,
            "conclusion": "价格数据不完整，暂时无法比较。",
        }
    if (
            target_price.currency
            and competitor_price.currency
            and target_price.currency.upper()
            != competitor_price.currency.upper()
    ):
        return {
            "target_price": target_price.amount,
            "competitor_price": competitor_price.amount,
            "price_difference": None,
            "price_difference_percent": None,
            "conclusion": "商品币种不同，请统一币种后再比较。",
        }

    target_amount = target_price.amount
    competitor_amount = competitor_price.amount

    difference = round(competitor_price.amount - target_price.amount,2)
    percentage = (
        round(difference / target_amount * 100, 2)
        if target_amount > 0
        else None
    )
    if difference > 0:
        conclusion = "竞品价格高于目标商品。"
    elif difference < 0:
        conclusion = "竞品价格低于目标商品。"
    else:
        conclusion = "两款商品价格相同。"
    return {
        "target_price": target_amount,
        "competitor_price": competitor_amount,
        "price_difference": difference,
        "price_difference_percent": percentage,
        "conclusion": conclusion,
    }

