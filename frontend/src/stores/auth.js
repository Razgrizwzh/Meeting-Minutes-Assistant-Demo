import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { TOKEN_KEY, USER_KEY } from '@/api/index'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // 以 localStorage 为真相源，启动时镜像到 store
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user?.username || '',
  },

  actions: {
    async login(username, password) {
      const { data } = await authApi.login(username, password)
      this._setSession(data.access_token, data.user)
    },

    async register(username, password) {
      // 后端注册即登录，返回 TokenOut
      const { data } = await authApi.register(username, password)
      this._setSession(data.access_token, data.user)
    },

    async logout() {
      try {
        await authApi.logout()
      } catch {
        // 后端登出失败不阻塞前端清 token
      }
      this._clearSession()
    },

    // 401 拦截器清了 localStorage 后，同步清 store 状态
    clearOnAuthError() {
      this.token = null
      this.user = null
    },

    _setSession(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },

    _clearSession() {
      this.token = null
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
