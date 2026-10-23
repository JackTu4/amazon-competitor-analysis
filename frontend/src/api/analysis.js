const BASE_URL = "/api"

export async function createAnalysis(targetProduct) {
  const response = await fetch(`${BASE_URL}/analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      target_product: targetProduct
    })
  })

  const data = await response.json()

  if (!response.ok) {
    console.error("FastAPI 返回的错误：", data)
    throw new Error(
      `创建任务失败：HTTP ${response.status}，${JSON.stringify(data.detail)}`
    )
  }

  return data
}
// 查询分析任务状态
export async function getAnalysisStatus(taskId) {
  const response = await fetch(`/api/analysis/${taskId}`)

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      `查询任务状态失败：HTTP ${response.status}`
    )
  }

  return data
}


// 获取 Markdown 分析报告
export async function getAnalysisReport(taskId) {
  const response = await fetch(
    `/api/analysis/${taskId}/report`
  )

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      `获取报告失败：HTTP ${response.status}`
    )
  }

  return data
}