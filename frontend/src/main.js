import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Element Plus 基础样式（组件 JS 由 unplugin 按需自动导入；
// 样式全局引入一次，确保 ElMessage 等动态组件样式就位）
import 'element-plus/dist/index.css'
// Element Plus 深色主题变量：配合 <html class="dark"> 生效
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// 在挂载前应用主题，避免首屏闪白/闪黑
import { useThemeStore } from './stores/theme'
useThemeStore(pinia).init()

app.mount('#app')
