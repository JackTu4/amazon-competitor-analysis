import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig({   //导出配置给vite去读取 没有这个导出配置的话 vite无法读取自定义地配置
  plugins: [vue()],

  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  }
})