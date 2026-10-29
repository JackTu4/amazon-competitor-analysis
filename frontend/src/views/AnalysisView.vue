<script setup>
import { ref, computed, onUnmounted } from "vue"
import MarkdownIt from "markdown-it"
import DOMPurify from "dompurify"
import AnalysisStatus from "../components/AnalysisStatus.vue"
import ProductForm from "../components/productForm.vue"

import {
  createAnalysis,
  getAnalysisStatus,
  getAnalysisReport
} from "../api/analysis.js"

const taskId = ref("")
const loading = ref(false)
const errorMessage = ref("")

// 新增：任务状态和报告内容
const taskStatus = ref("")
const report = ref("")
// Markdown 渲染器
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

// Markdown 转换为安全 HTML
const renderedReport = computed(() => {
  const html = md.render(report.value || "")
  return DOMPurify.sanitize(html)
})

// 下载 Markdown 报告
function downloadReport() {
  if (!report.value) {
    return
  }

  const blob = new Blob(
    [report.value],
    { type: "text/markdown;charset=utf-8" }
  )

  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")

  a.href = url
  a.download = `competitor-report-${taskId.value}.md`

  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  URL.revokeObjectURL(url)
}

// 将后端返回的 Markdown 转换成安全的 HTML
let pollTimer = null
let requestVersion = 0

function stopPolling() {
  if (pollTimer !== null) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

// 每隔 2 秒查询一次任务状态
async function pollStatus(id, version) {
  if (version !== requestVersion) return

  try {
    const result = await getAnalysisStatus(id)

    if (version !== requestVersion) return

    taskStatus.value = result.status

    if (result.status === "completed") {
      const reportResult = await getAnalysisReport(id)

      if (version !== requestVersion) return

      report.value = reportResult.report
      loading.value = false
      return
    }

    if (result.status === "failed") {
      errorMessage.value = result.error || "分析任务失败"
      loading.value = false
      return
    }

    // pending 或 running，2 秒后继续查询
    pollTimer = setTimeout(() => {
      pollStatus(id, version)
    }, 2000)

  } catch (error) {
    if (version !== requestVersion) return

    errorMessage.value = error.message || "查询任务失败"
    loading.value = false
  }
}

async function startAnalysis(product) {
  product = product.trim()

  if (!product || loading.value) {
    if (!product) {
      errorMessage.value = "请输入商品名称或 ASIN"
    }
    return
  }

  stopPolling()
  const version = ++requestVersion

  loading.value = true
  errorMessage.value = ""
  taskId.value = ""
  taskStatus.value = ""
  report.value = ""

  try {
    const result = await createAnalysis(product)

    if (version !== requestVersion) return

    taskId.value = result.task_id
    taskStatus.value = result.status

    await pollStatus(result.task_id, version)

  } catch (error) {
    if (version !== requestVersion) return

    errorMessage.value = error.message || "创建任务失败"
    loading.value = false
  }
}

onUnmounted(() => {
  requestVersion++
  stopPolling()
})
</script>

<template>
  <div class="container">

    <h1>Amazon 智能竞品分析系统</h1>

    <p class="description">
      输入目标商品名称，自动发现并分析竞品。
    </p>

 <!-- 商品输入组件 -->
    <ProductForm
      :loading="loading"
      @submit="startAnalysis"
    />

    <!-- 分析状态组件 -->
    <AnalysisStatus
      :task-id="taskId"
      :task-status="taskStatus"
      :error-message="errorMessage"
    />

    <!-- Markdown 分析报告 -->
<div v-if="report" class="report">

  <div class="report-toolbar">
    <button
      type="button"
      class="download-button"
      @click="downloadReport"
    >
      下载 Markdown 报告
    </button>
  </div>

  <div
    class="markdown-body"
    v-html="renderedReport"
  ></div>

</div>

  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 60px auto;
  padding: 0 20px;
  font-family: Arial, sans-serif;
}

h1 {
  font-size: 32px;
  color: #242424;
  margin-bottom: 20px;
}

.description {
  font-size: 16px;
  color: #555;
  margin-bottom: 30px;
}

/* 分析报告区域 */
.report {
  margin-top: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

/* 保留 Markdown 原文换行 */
.markdown-body {
  line-height: 1.8;
  color: #333;
  overflow-wrap: anywhere;
}

.markdown-body :deep(h1) {
  font-size: 28px;
  margin-bottom: 20px;
}

.markdown-body :deep(h2) {
  font-size: 22px;
  margin-top: 24px;
  margin-bottom: 12px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.markdown-body :deep(h3) {
  font-size: 18px;
  margin-top: 20px;
}

.markdown-body :deep(ul) {
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin-bottom: 8px;
}

.markdown-body :deep(p) {
  margin-bottom: 12px;
}

.markdown-body :deep(pre) {
  overflow-x: auto;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
}
.report-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.download-button {
  padding: 10px 18px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.download-button:hover {
  background: #1d4ed8;
}
</style>