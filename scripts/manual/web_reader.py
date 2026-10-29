import sys
from pathlib import Path

# 允许直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.tools.web_reader import read_webpage
def test_read_webpage():
    url="https://example.com"
    text=read_webpage(url)
    print(text)
test_read_webpage()