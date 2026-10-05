from app.models.competitor import Report
from app.models.competitor import CompetitorAnalysis
from tests.test_competitor import analysis
report=Report(
    title="HUADISK vs Samsung SSD竞品分析",
    analysis=analysis,
    summary="Samsung品牌影响力更强，HUADISK价格优势明显"
)
print(report)