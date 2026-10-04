from app.tools.web_reader import read_webpage
def test_read_webpage():
    url="https://example.com"
    text=read_webpage(url)
    print(text)
test_read_webpage()