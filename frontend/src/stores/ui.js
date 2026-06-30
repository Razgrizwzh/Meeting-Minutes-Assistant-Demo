import { defineStore } from 'pinia'

// UI 状态 store：管理登录/注册弹窗可见性等，避免组件间 prop 钻取
export const useUiStore = defineStore('ui', {
  state: () => ({
    authDialogVisible: false,
    // 'login' | 'register'
    authMode: 'login',
    sidebarCollapsed: false,
  }),

  actions: {
    openAuth(mode = 'login') {
      this.authMode = mode
      this.authDialogVisible = true
    },
    closeAuth() {
      this.authDialogVisible = false
    },
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
  },
})
