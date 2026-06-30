<script setup>
import MeetingInput from '@/components/MeetingInput.vue'
import MinutesView from '@/components/MinutesView.vue'
import ChatPanel from '@/components/ChatPanel.vue'
</script>

<template>
  <div class="main-view">
    <MeetingInput />
    <MinutesView />
    <ChatPanel />
  </div>
</template>

<style scoped>
.main-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}
</style>