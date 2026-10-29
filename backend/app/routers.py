from fastapi import APIRouter, Depends, HTTPException
from backend.app.schemas import (
    AnalysisRequest,
    AnalysisResponse,
)
from backend.app.security import require_api_key

from backend.app.services.analysis_service import (
    create_analysis_task,
)
from backend.app.services.report_service import get_analysis_report
from backend.app.services.result_service import get_analysis_products
from backend.app.services.task_service import get_analysis_task
# 创建路由对象（整个 /api 挂载 API Key 鉴权）
router = APIRouter(
    prefix="/api",
    tags=["Analysis"],
    dependencies=[Depends(require_api_key)],
)


# 1. 创建分析任务
@router.post("/analysis", response_model=AnalysisResponse)
def create_analysis(request: AnalysisRequest):

    target_product = request.target_product.strip()

    if not target_product:
        raise HTTPException(
            status_code=422,
            detail="目标商品名称不能为空",
        )

    task_id = create_analysis_task(target_product) #接收到Swagger UI请求，生成task.id 还未使用前端

    return AnalysisResponse(
        task_id=task_id,
        status="pending",
        message="分析任务已提交，请查询任务状态",
        target_product=target_product,
    )


# 2. 查询任务状态
@router.get("/analysis/{task_id}")
def get_analysis_status(task_id: str):

    record = get_analysis_task(task_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="未找到该分析任务",
        )

    return record


# 3. 获取分析报告
@router.get("/analysis/{task_id}/report")
def get_analysis_report_api(task_id: str):
    """从 MySQL 查询分析报告。"""

    # 1. 查询任务是否存在
    task = get_analysis_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="未找到该分析任务",
        )

    # 2. 判断任务状态
    if task["status"] != "completed":
        return {
            "task_id": task_id,
            "status": task["status"],
            "report": None,
            "error": task["error"],
        }

    # 3. 从 MySQL 查询报告
    report = get_analysis_report(task_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="任务已完成，但未找到报告",
        )

    # 4. 返回报告内容
    return {
        "task_id": task_id,
        "status": "completed",
        "report": report["report"],
        "error": None,
    }


# 4. 获取任务下的商品明细（目标商品 + 竞品 + 来源）
@router.get("/analysis/{task_id}/products")
def get_analysis_products_api(task_id: str):
    """从 MySQL 查询任务落库的商品与来源。"""

    task = get_analysis_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="未找到该分析任务",
        )

    return {
        "task_id": task_id,
        "status": task["status"],
        "products": get_analysis_products(task_id),
    }

