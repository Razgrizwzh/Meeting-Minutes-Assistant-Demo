import { defineStore } from 'pinia'

// UI 状态 store：管理登录/注册弹窗可见性等，避免组件间 prop 钻取
export const useUiStore = defineStore('ui', {
  state: () => ({
    authDialogVisible: false,
    // 'login' | 'register'
    authMode: 'login',
    sidebarCollapsed: false,
    // 会议输入区是否收起（收起后只剩标题栏，给下方 Tab 内容区让出纵向空间）
    inputCollapsed: false,
    // 主区当前激活的 Tab：'minutes' | 'chat'
    activeMainTab: 'minutes',
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
    toggleInputCollapsed() {
      this.inputCollapsed = !this.inputCollapsed
    },
    setActiveMainTab(tab) {
      this.activeMainTab = tab
    },
  },
})
