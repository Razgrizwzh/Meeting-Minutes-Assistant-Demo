<script setup>
import MeetingInput from '@/components/MeetingInput.vue'
import MinutesView from '@/components/MinutesView.vue'
</script>

<template>
  <div class="main-view">
    <MeetingInput />
    <MinutesView />
    <section class="placeholder-card chat-area">
      <h3>对话追问</h3>
      <p class="ph-hint">占位：多轮对话气泡 —— 基于 RAG 的追问（后续轮实现）</p>
    </section>
  </div>
</template>

<style scoped>
.main-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}
.chat-area {
  background: var(--ma-surface);
  border: 1px solid var(--ma-border);
  border-radius: var(--ma-radius);
  padding: 16px 20px;
  min-height: 120px;
}
.chat-area h3 {
  margin: 0 0 8px;
  font-size: 16px;
}
.chat-area .ph-hint {
  color: var(--ma-text-secondary);
  font-size: 13px;
}
</style>
