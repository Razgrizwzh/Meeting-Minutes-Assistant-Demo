import axios from 'axios'
import { ElMessage } from 'element-plus'

// localStorage 键名
const TOKEN_KEY = 'ma_token'
const USER_KEY = 'ma_user'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截：附加 JWT
// 注意：直接从 localStorage 读 token（而非导入 Pinia store），
// 避免模块作用域循环依赖；store 在初始化时从 localStorage 镜像。
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截：401 自动登出
// 【安全取舍】JWT 存 localStorage 有 XSS 暴露风险；本地 demo 可接受，
// 生产环境应改用 HttpOnly cookie + CSRF 防护。
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      // 用自定义事件通知 store/UI（避免直接导入 store 造成循环依赖）
      window.dispatchEvent(new CustomEvent('auth:logout'))
      ElMessage.error('登录已过期，请重新登录')
    }
    return Promise.reject(error)
  },
)

export default http
export { TOKEN_KEY, USER_KEY }
