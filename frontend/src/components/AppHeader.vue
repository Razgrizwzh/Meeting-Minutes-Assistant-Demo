<script setup>
import { User, SwitchButton, Sunny, Moon } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const ui = useUiStore()
const theme = useThemeStore()

async function handleLogout() {
  await auth.logout()
  ElMessage.success('已登出')
}

function openLogin() {
  ui.openAuth('login')
}
</script>

<template>
  <header class="app-header">
    <div class="brand">
      <span class="logo">📝</span>
      <span class="app-name">会议纪要助手</span>
    </div>

    <div class="header-right">
      <!-- 主题切换 -->
      <el-button
        class="theme-btn"
        circle
        :icon="theme.isDark ? Sunny : Moon"
        :title="theme.isDark ? '切换到浅色模式' : '切换到深色模式'"
        @click="theme.toggle"
      />
      <template v-if="auth.isLoggedIn">
        <el-dropdown trigger="click">
          <span class="user-trigger">
            <el-icon><User /></el-icon>
            <span class="username">{{ auth.username }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                <span>登出</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template v-else>
        <el-button type="primary" @click="openLogin">登录 / 注册</el-button>
      </template>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: var(--ma-header-h);
  background: var(--ma-surface);
  border-bottom: 1px solid var(--ma-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 0 var(--ma-border-light);
  transition: background-color 0.25s ease, border-color 0.25s ease;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo {
  font-size: 20px;
}
.app-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--ma-text);
  letter-spacing: 0.5px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.theme-btn {
  color: var(--ma-text-secondary);
}
.theme-btn:hover {
  color: var(--ma-primary);
}
.user-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: var(--ma-radius-sm);
  color: var(--ma-text);
  transition: background-color 0.2s ease;
}
.user-trigger:hover {
  background: var(--ma-primary-light);
}
.username {
  font-size: 14px;
}
</style>
