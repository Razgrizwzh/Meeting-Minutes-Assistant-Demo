<script setup>
import { onMounted, onUnmounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import AuthDialog from '@/components/AuthDialog.vue'
import MainView from '@/views/MainView.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// 监听 axios 401 拦截器发出的登出事件，同步清空 store 状态
function onAuthLogout() {
  auth.clearOnAuthError()
}

onMounted(() => window.addEventListener('auth:logout', onAuthLogout))
onUnmounted(() => window.removeEventListener('auth:logout', onAuthLogout))
</script>

<template>
  <div class="app-layout">
    <AppHeader />
    <div class="app-body">
      <AppSidebar />
      <main class="app-main">
        <MainView />
      </main>
    </div>
  </div>
  <AuthDialog />
</template>
