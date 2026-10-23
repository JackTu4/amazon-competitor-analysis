<script setup>
defineProps({
  taskId: {
    type: String,
    default: ""
  },

  taskStatus: {
    type: String,
    default: ""
  },

  errorMessage: {
    type: String,
    default: ""
  }
})
</script>

<template>
  <div>
    <!-- 任务创建成功 -->
    <div v-if="taskId" class="success">
      <h3>任务创建成功！</h3>

      <p>任务 ID：</p>
      <p class="task-id">{{ taskId }}</p>
    </div>

    <!-- 显示任务状态 -->
    <div v-if="taskStatus" class="status">
      <h3>分析状态</h3>

      <p v-if="taskStatus === 'pending'">
        等待执行...
      </p>

      <p v-else-if="taskStatus === 'running'">
        正在分析商品，请稍候...
      </p>

      <p v-else-if="taskStatus === 'completed'">
        分析完成！
      </p>

      <p v-else-if="taskStatus === 'failed'">
        分析失败
      </p>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<style scoped>
.success {
  margin-top: 30px;
  padding: 20px;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 8px;
}

.success h3 {
  color: #166534;
  margin-top: 0;
}

.task-id {
  overflow-wrap: anywhere;
  font-family: monospace;
}

.status {
  margin-top: 24px;
  padding: 16px;
  background: #eff6ff;
  border-radius: 8px;
}

.error {
  margin-top: 20px;
  padding: 12px;
  color: #b91c1c;
  background: #fef2f2;
  border-radius: 6px;
}
</style>