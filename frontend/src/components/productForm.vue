<script setup>
import { ref } from "vue"

// 接收父组件传来的加载状态
defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

// 声明组件可以向父组件发送的事件
const emit = defineEmits(["submit"])

// 商品输入内容
const targetProduct = ref("")

function handleSubmit() {
  const product = targetProduct.value.trim()

  if (!product) {
    alert("请输入商品名称或 ASIN")
    return
  }

  // 把商品名称交给父组件处理
  emit("submit", product)
}
</script>

<template>
  <div class="form">
    <label for="product">
      目标商品名称或 ASIN
    </label>

    <input
      id="product"
      v-model="targetProduct"
      type="text"
      placeholder="例如：HUADISK 256GB SSD"
      @keyup.enter="handleSubmit"
    />

    <button
      type="button"
      @click="handleSubmit"
      :disabled="loading"
    >
      {{ loading ? "分析中..." : "开始竞品分析" }}
    </button>
  </div>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

label {
  font-size: 16px;
  font-weight: 500;
}

input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

button {
  width: fit-content;
  padding: 12px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

button:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
</style>