const BASE_URL = "/api"

// 后端在项目根目录 .env 里配置 API_KEY 后，
// 前端通过 frontend/.env 的 VITE_API_KEY 携带同一个值
const API_KEY = import.meta.env.VITE_API_KEY || ""

function authHeaders(extra = {}) {
  const headers = { ...extra }

  if (API_KEY) {
    headers["X-API-Key"] = API_KEY
  }

  return headers
}

function errorDetail(data, status) {
  if (status === 401) {
    return "未通过身份校验，请检查 API_KEY 与 VITE_API_KEY 是否一致"
  }

  return data && data.detail ? data.detail : `HTTP ${status}`
}

export async function createAnalysis(targetProduct) {
  const response = await fetch(`${BASE_URL}/analysis`, {
    method: "POST",
    headers: authHeaders({
      "Content-Type": "application/json"
    }),
    body: JSON.stringify({
      target_product: targetProduct
    })
  })

  const data = await response.json()

  if (!response.ok) {
    console.error("FastAPI 返回的错误：", data)
    throw new Error(
      `创建任务失败：${errorDetail(data, response.status)}`
    )
  }

  return data
}
// 查询分析任务状态
export async function getAnalysisStatus(taskId) {
  const response = await fetch(`/api/analysis/${taskId}`, {
    headers: authHeaders()
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      `查询任务状态失败：${errorDetail(data, response.status)}`
    )
  }

  return data
}


// 获取 Markdown 分析报告
export async function getAnalysisReport(taskId) {
  const response = await fetch(
    `/api/analysis/${taskId}/report`,
    {
      headers: authHeaders()
    }
  )

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      `获取报告失败：${errorDetail(data, response.status)}`
    )
  }

  return data
}
