<script setup>
import { ref, nextTick, computed } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import { useMeetingStore } from '@/stores/meeting'

const meeting = useMeetingStore()

const input = ref('')
const scrollRef = ref(null)

const canAsk = computed(() => meeting.hasMinutes && !meeting.asking)

async function scrollToBottom() {
  await nextTick()
  const el = scrollRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function handleSend() {
  const q = input.value.trim()
  if (!q || !meeting.hasMinutes || meeting.asking) return
  input.value = ''
  try {
    await meeting.sendQuery(q)
  } catch {
    // 错误消息已由 store 推入 chatHistory
  }
  await scrollToBottom()
}

function onEnter() {
  handleSend()
}

function handleEnterKey(e) {
  // Enter 发送，Shift+Enter 换行
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    onEnter()
  }
}
</script>

<template>
  <section class="chat-panel">
    <div class="panel-header">
      <h3>对话追问</h3>
      <span class="panel-hint" v-if="meeting.hasMinutes">基于 RAG 检索当前/历史会议</span>
      <span class="panel-hint" v-else>请先生成纪要</span>
    </div>

    <div class="messages" ref="scrollRef">
      <el-empty
        v-if="meeting.chatHistory.length === 0"
        :description="meeting.hasMinutes ? '输入问题对当前会议提问（Enter 发送 / Shift+Enter 换行）' : '请先生成会议纪要再追问'"
        :image-size="60"
      />

      <template v-else>
        <div
          v-for="(msg, i) in meeting.chatHistory"
          :key="i"
          class="bubble"
          :class="msg.role === 'user' ? 'bubble-user' : 'bubble-ai'"
        >
          <div class="bubble-content">{{ msg.content }}</div>
          <div v-if="msg.sources && msg.sources.length" class="sources">
            <span class="sources-label">来源：</span>
            <el-tag
              v-for="(s, j) in msg.sources"
              :key="j"
              size="small"
              type="info"
              effect="plain"
            >
              {{ s.meeting_name || '未命名' }}{{ s.date ? ' · ' + s.date : '' }}
            </el-tag>
          </div>
        </div>
      </template>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        :disabled="!meeting.hasMinutes"
        placeholder="输入你的问题…"
        resize="none"
        @keydown="handleEnterKey"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="meeting.asking"
        :disabled="!canAsk"
        @click="handleSend"
      >
        发送
      </el-button>
    </div>
  </section>
</template>

<style scoped>
.chat-panel {
  background: var(--ma-surface);
  border: 1px solid var(--ma-border);
  border-radius: var(--ma-radius);
  padding: 16px 20px;
  flex: 1 1 0;
  min-height: 220px;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;
}
.panel-header h3 {
  margin: 0;
  font-size: 16px;
}
.panel-hint {
  font-size: 12px;
  color: var(--ma-text-secondary);
}
.messages {
  flex: 1;
  overflow: auto;
  padding: 4px 4px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 120px;
}
.bubble {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.bubble-user {
  align-self: flex-end;
}
.bubble-ai {
  align-self: flex-start;
}
.bubble-content {
  padding: 10px 14px;
  border-radius: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}
.bubble-user .bubble-content {
  background: var(--ma-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.bubble-ai .bubble-content {
  background: #f0f2f5;
  color: var(--ma-text);
  border-bottom-left-radius: 4px;
}
.sources {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  font-size: 11px;
}
.sources-label {
  color: var(--ma-text-secondary);
}
.chat-input {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.chat-input .el-input {
  flex: 1;
}
</style>