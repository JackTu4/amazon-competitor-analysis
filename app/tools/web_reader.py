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
    response=requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')
    text=soup.get_text(separator='\n',strip=True)
    return {
        "text":text,
        "url":url
    }  #  返回经过处理之后的纯文本形式