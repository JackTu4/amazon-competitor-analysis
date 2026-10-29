import sys
from pathlib import Path

# 允许直接运行：把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.models.competitor import Report
from app.models.competitor import CompetitorAnalysis
from test_competitor import analysis
report=Report(
    title="HUADISK vs Samsung SSD竞品分析",
    analysis=analysis,
    summary="Samsung品牌影响力更强，HUADISK价格优势明显"
)
print(report)