from app.models.extraction import Price
from app.analyzers.price_analyzer import analyze_price


def test_analyze_price():
    target = Price(amount=50.0, currency="USD")
    competitor = Price(amount=60.0, currency="USD")

    result = analyze_price(target, competitor)

    assert result["price_difference"] == 10.0
    assert result["price_difference_percent"] == 20.0
    assert result["conclusion"] == "竞品价格高于目标商品。"


def test_missing_price():
    target = Price(amount=50.0, currency="USD")

    result = analyze_price(target, None)

    assert result["price_difference"] is None


def test_different_currency():
    target = Price(amount=50.0, currency="USD")
    competitor = Price(amount=60.0, currency="JPY")

    result = analyze_price(target, competitor)

    assert result["price_difference"] is None
    assert "币种不同" in result["conclusion"]

def test_same_price():
    target = Price(amount=50.0, currency="USD")
    competitor = Price(amount=50.0, currency="USD")

    result = analyze_price(target, competitor)

    assert result["price_difference"] == 0
    assert result["conclusion"] == "两款商品价格相同。"


def test_zero_target_price():
    target = Price(amount=0.0, currency="USD")
    competitor = Price(amount=60.0, currency="USD")

    result = analyze_price(target, competitor)

    assert result["price_difference"] == 60.0
    assert result["price_difference_percent"] is None
    assert result["conclusion"] == "竞品价格高于目标商品。"
