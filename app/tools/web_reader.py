import requests
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
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language":
            "en-US,en;q=0.9",
        "Accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    session = requests.Session()
    response = session.get(
        url,
        headers=headers,
        timeout=10
    )
    if response.status_code != 200:
        raise Exception(
            f"网页请求失败:{response.status_code}"
        )
    soup = BeautifulSoup(response.content, 'html.parser')
    text=soup.get_text(separator='\n',strip=True)
    if "Continue shopping" in text:
        raise Exception(
            "Amazon返回验证页面"
        )
    if text is None or len(text) == 0:
        raise Exception(
            "网页没有有效文本"
        )
    return {
        "text":text,
        "url":url
    }  #  返回经过处理之后的纯文本形式