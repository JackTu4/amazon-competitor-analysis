"""工作流的结构化产出。

除了报告路径，还要把商品明细和失败原因一并交回调用方，
由 backend 层负责落库与展示。
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WorkflowResult:
    report_path: Path | str
    target_product: str
    task_id: str | None = None
    target_asin: str | None = None

    # 每个元素形如：
    # {"competitor_name": ..., "competitor_asin": ..., "competitor_url": ...,
    #  "analysis": CompetitorAnalysis | {"error": ...}}
    analyses: list[dict] = field(default_factory=list)

    # 分析失败或被跳过的竞品，用于报告展示和降级监控
    failures: list[dict] = field(default_factory=list)

    @property
    def is_degraded(self) -> bool:
        return bool(self.failures)
