<script setup>
import { ref, nextTick, computed, watch, inject, onMounted, onBeforeUnmount } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { useMeetingStore } from '@/stores/meeting'

const meeting = useMeetingStore()

// markdown-it：渲染 AI 回答中的 **加粗** / - 列表 / `代码` / 链接 等，
// 让回答不再是混杂 "**" "-" 的纯文本。与 MinutesView 配置一致。
// 【安全取舍】demo 信任 LLM 输出，未做 HTML sanitize；
// 生产环境应对 v-html 内容做 DOMPurify 等过滤防 XSS。
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

const input = ref('')
const scrollRef = ref(null)
// el-input 实例 ref：供「针对内容提问」按钮聚焦
const inputRef = ref(null)

// 由 MainView 注入：注册聚焦函数；组件卸载时清空，避免切 Tab 后引用失效
const registerChatFocus = inject('registerChatFocus', null)
onMounted(() => {
  if (registerChatFocus) {
    registerChatFocus(() => inputRef.value?.focus?.())
  }
})
onBeforeUnmount(() => {
  if (registerChatFocus) registerChatFocus(null)
})

const canAsk = computed(() => meeting.hasMinutes && !meeting.asking)

async function scrollToBottom() {
  await nextTick()
  const el = scrollRef.value
  if (el) el.scrollTop = el.scrollHeight
}

// 流式问答时，AI 气泡 content 持续增长 -> 跟随滚到底
watch(
  () => meeting.chatHistory.length + (meeting.chatHistory.at(-1)?.content?.length || 0),
  scrollToBottom,
)

async function handleSend() {
  const q = input.value.trim()
  if (!q || !meeting.hasMinutes || meeting.asking) return
  input.value = ''
  try {
    meeting.sendQuery(q)  // 流式：不 await，watch 负责滚动
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
          <div
            v-if="msg.role === 'assistant'"
            class="bubble-content chat-markdown"
          >
            <span v-if="msg.content" v-html="renderMarkdown(msg.content)" />
            <span v-else class="typing">正在生成回答…</span>
          </div>
          <div v-else class="bubble-content">{{ msg.content }}</div>
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
        ref="inputRef"
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
  box-shadow: var(--ma-shadow);
  flex: 1 1 0;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
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
  gap: 12px;
  min-height: 120px;
}
.bubble {
  max-width: 80%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  /* 气泡入场动画 */
  animation: bubble-in 0.22s ease;
}
@keyframes bubble-in {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
.bubble-user {
  align-self: flex-end;
}
.bubble-ai {
  align-self: flex-start;
}
.bubble-content {
  padding: 10px 14px;
  border-radius: 14px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}
.bubble-user .bubble-content {
  background: var(--ma-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}
.bubble-ai .bubble-content {
  background: var(--ma-surface-2);
  color: var(--ma-text);
  border: 1px solid var(--ma-border-light);
  border-bottom-left-radius: 4px;
}
/* AI 回答按 Markdown 渲染：重置 pre-wrap，让 <p>/<ul> 自然排版 */
.chat-markdown {
  white-space: normal;
}
.chat-markdown :deep(p) {
  margin: 4px 0;
}
.chat-markdown :deep(p:first-child) {
  margin-top: 0;
}
.chat-markdown :deep(p:last-child) {
  margin-bottom: 0;
}
.chat-markdown :deep(ul),
.chat-markdown :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.chat-markdown :deep(li) {
  margin: 2px 0;
}
.chat-markdown :deep(strong) {
  font-weight: 600;
}
.chat-markdown :deep(code) {
  background: var(--ma-border-light);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.9em;
}
.chat-markdown :deep(a) {
  color: var(--ma-primary);
  text-decoration: none;
}
.chat-markdown :deep(a:hover) {
  text-decoration: underline;
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
.typing {
  color: var(--ma-text-secondary);
  font-style: italic;
}
.chat-input {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--ma-border-light);
}
.chat-input .el-input {
  flex: 1;
}
</style>