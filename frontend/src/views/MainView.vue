<script setup>
import { ref, provide, nextTick } from 'vue'
import MeetingInput from '@/components/MeetingInput.vue'
import MinutesView from '@/components/MinutesView.vue'
import ChatPanel from '@/components/ChatPanel.vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()

// ChatPanel 挂载时把自身 focus 方法注册进来；卸载时置空。
// 用「注册式」而非跨组件 ref，规避 el-tabs 切换时 pane 卸载导致引用失效的时序问题。
const focusChatInput = ref(null)
provide('registerChatFocus', (fn) => {
  focusChatInput.value = fn
})

// 切到 Chat Tab 并聚焦输入框（供 MinutesView「针对内容提问」按钮调用）
function switchToChat() {
  ui.setActiveMainTab('chat')
  // 等待 ChatPanel 挂载完成（切 Tab 触发 v-if 渲染），再聚焦
  nextTick().then(() => {
    focusChatInput.value?.()
  })
}
provide('switchToChat', switchToChat)
</script>

<template>
  <div class="main-view">
    <MeetingInput />
    <section class="main-tabs">
      <el-tabs v-model="ui.activeMainTab" class="content-tabs">
        <el-tab-pane label="会议纪要" name="minutes">
          <MinutesView />
        </el-tab-pane>
        <el-tab-pane label="Chat" name="chat">
          <ChatPanel />
        </el-tab-pane>
      </el-tabs>
    </section>
  </div>
</template>

<style scoped>
.main-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  /* 撑满 app-main 高度，Tab 区才能正确吃掉剩余空间 */
  min-height: 100%;
  height: 100%;
}
.main-tabs {
  flex: 1 1 0;
  min-height: 0; /* flex 子项允许收缩，让内部 overflow 生效 */
  display: flex;
  flex-direction: column;
  background: var(--ma-surface);
  border: 1px solid var(--ma-border);
  border-radius: var(--ma-radius);
  box-shadow: var(--ma-shadow);
  overflow: hidden;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
/* el-tabs 自身要撑满父高度，其内容区才能滚动 */
.content-tabs {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0 20px 16px;
}
/* Tab 头部样式：去掉默认灰底，加分隔线 */
.content-tabs :deep(.el-tabs__header) {
  margin: 0 0 12px;
  padding: 0 20px;
  background: var(--ma-surface);
}
.content-tabs :deep(.el-tabs__nav-wrap)::after {
  background-color: var(--ma-border-light);
  height: 1px;
}
.content-tabs :deep(.el-tabs__item) {
  height: 44px;
  font-size: 15px;
  font-weight: 500;
}
.content-tabs :deep(.el-tabs__content) {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.content-tabs :deep(.el-tab-pane) {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
/* Tab 内的子面板融入 Tab 卡片：去掉各自的外层边框/背景/阴影/圆角，
   只保留内容，由 .main-tabs 统一提供卡片外观 */
.content-tabs :deep(.minutes-view),
.content-tabs :deep(.chat-panel) {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
}
</style>
