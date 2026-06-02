import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'


// 导出 Vite 配置
export default defineConfig({
  plugins: [vue()], // 启用 Vue 插件，让Vite能编译 .vue 文件
})
