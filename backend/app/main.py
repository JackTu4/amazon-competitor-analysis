
from pathlib import Path

from fastapi import FastAPI, HTTPException

from backend.app.schemas import AnalysisRequest, AnalysisResponse
from backend.app.analysis_service import (
    analysis_tasks,
    create_analysis_task,
)


app = FastAPI(
    title="Amazon 智能竞品分析系统",
    description="提供商品竞品分析任务和报告查询接口",
    version="0.1.0",
)


# 1. 健康检查接口
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Amazon 竞品分析后端运行正常",
    }


# 2. 创建分析任务
@app.post("/api/analysis", response_model=AnalysisResponse)
def create_analysis(request: AnalysisRequest):

    target_product = request.target_product.strip()

    if not target_product:
        raise HTTPException(
            status_code=422,
            detail="目标商品名称不能为空",
        )

    task_id = create_analysis_task(target_product)

    return AnalysisResponse(
        task_id=task_id,
        status="pending",
        message="分析任务已提交，请查询任务状态",
        target_product=target_product,
    )


# 3. 查询任务状态
@app.get("/api/analysis/{task_id}")
def get_analysis_status(task_id: str):

    record = analysis_tasks.get(task_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="未找到该分析任务",
        )

    return {
        "task_id": record["task_id"],
        "target_product": record["target_product"],
        "status": record["status"],
        "error": record["error"],
    }


# 4. 获取分析报告
@app.get("/api/analysis/{task_id}/report")
def get_analysis_report(task_id: str):

    record = analysis_tasks.get(task_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="未找到该分析任务",
        )

    if record["status"] == "failed":
        raise HTTPException(
            status_code=409,
            detail=record["error"] or "分析任务执行失败",
        )

    if record["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail="分析任务尚未完成",
        )

    report_path = record["result"]

    if not isinstance(report_path, (str, Path)):
        raise HTTPException(
            status_code=500,
            detail="工作流没有返回有效的报告路径",
        )

    path = Path(report_path)

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="报告文件不存在",
        )

    markdown = path.read_text(encoding="utf-8")

    return {
        "task_id": task_id,
        "status": "completed",
        "report": markdown,
    }
