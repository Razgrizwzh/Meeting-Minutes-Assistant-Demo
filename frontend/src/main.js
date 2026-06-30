import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Element Plus 基础样式（组件 JS 由 unplugin 按需自动导入；
// 样式全局引入一次，确保 ElMessage 等动态组件样式就位）
import 'element-plus/dist/index.css'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
