from app.reporter.markdown import generate_markdown
class MockProduct:
    def __init__(self, name, rating):
        self.name = name
        self.rating = rating
class MockReporter:
    def __init__(self):
        self.target_product=MockProduct(
            "huadisk",
            4.5
        )
        self.competitor=MockProduct(
            "sumsam",
            4.7
        )
        self.summary="huadisk价格更低,sumsam影响力更强"
def test_generate_markdown():
    data=MockReporter()
    result=generate_markdown(data)
    print(result)
    assert "huadisk" in result
    assert "sumsam" in result
    assert "4.5" in result
    assert "价格更低" in result
