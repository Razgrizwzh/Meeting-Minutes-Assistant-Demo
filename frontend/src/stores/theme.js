import { defineStore } from 'pinia'

// 主题 store：light / dark，持久化到 localStorage，首次按系统偏好初始化。
const THEME_KEY = 'ma_theme'

function detectInitial() {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  // 未设过：跟随系统偏好
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

// 把主题应用到 <html> 的 class，并同步 EP 深色变量所需的 html.dark
function applyTheme(theme) {
  const el = document.documentElement
  if (theme === 'dark') el.classList.add('dark')
  else el.classList.remove('dark')
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: detectInitial(),
  }),

  getters: {
    isDark: (state) => state.theme === 'dark',
  },

  actions: {
    // 在 app 启动时调用一次，把初始主题落到 <html>
    init() {
      applyTheme(this.theme)
    },
    toggle() {
      this.set(this.theme === 'dark' ? 'light' : 'dark')
    },
    set(theme) {
      this.theme = theme
      localStorage.setItem(THEME_KEY, theme)
      applyTheme(theme)
    },
  },
})
