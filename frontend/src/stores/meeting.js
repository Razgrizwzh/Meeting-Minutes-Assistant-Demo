import { defineStore } from 'pinia'
import * as meetingsApi from '@/api/meetings'
import * as chatApi from '@/api/chat'
import { v4 as uuidv4 } from 'uuid'

const SESSION_ID_KEY = 'ma_session_id'

export const useMeetingStore = defineStore('meeting', {
  state: () => ({
    // 当前展示的纪要
    currentMeetingId: null,
    currentMinutes: null, // 结构化 JSON
    currentMarkdown: '', // 渲染好的 Markdown 字符串
    generating: false,
    inputLength: 0, // 最近一次生成输入的文本长度（供进度组件预估时长）
    // 历史列表（登录后）
    history: [],
    loadingHistory: false,
    // RAG 对话
    chatHistory: [], // [{role:'user'|'assistant', content, sources?}]
    asking: false,
  }),

  getters: {
    hasMinutes: (state) => !!state.currentMinutes,
    // 稳定 sessionId（localStorage，未登录也保留），用于 RAG 会话隔离
    sessionId: () => {
      let sid = localStorage.getItem(SESSION_ID_KEY)
      if (!sid) {
        sid = uuidv4()
        localStorage.setItem(SESSION_ID_KEY, sid)
      }
      return sid
    },
  },

  actions: {
    // 生成纪要：payload { text?, file?, meetingName?, date? }
    async generate(payload) {
      this.generating = true
      this.inputLength = payload.file ? payload.file.size || 0 : (payload.text || '').length
      try {
        const { data } = await meetingsApi.generateMeeting({ ...payload, sessionId: this.sessionId })
        this.currentMeetingId = data.meeting_id
        this.currentMinutes = data.minutes
        this.currentMarkdown = data.markdown
        // 生成新纪要时清空上一轮对话
        this.clearChat()
        // 登录用户生成后刷新历史列表
        if (data.meeting_id) {
          this.loadHistory().catch(() => {})
        }
        return data
      } finally {
        this.generating = false
      }
    },

    async loadHistory() {
      this.loadingHistory = true
      try {
        const { data } = await meetingsApi.listHistory()
        this.history = data
      } finally {
        this.loadingHistory = false
      }
    },

    // 从历史会议加载详情到当前展示
    async loadMeeting(meetingId) {
      const { data } = await meetingsApi.getMeeting(meetingId)
      this.currentMeetingId = data.meeting_id
      this.currentMinutes = data.minutes
      this.currentMarkdown = data.markdown
      // 切换会议：先清空，再尝试从后端拉该会议的持久化对话
      this.clearChat()
      await this.loadChat()
      return data
    },

    // 加载当前会议的持久化对话（登录用户）。匿名无 meeting_id 则保持空。
    async loadChat() {
      const mid = this.currentMeetingId
      if (!mid) return
      try {
        const { data } = await chatApi.getHistory(mid)
        this.chatHistory = data.messages || []
      } catch {
        // 拉取失败（如 401/404）则保持空对话，不打扰用户
        this.chatHistory = []
      }
    },

    // 删除历史会议：从列表移除；若删的正是当前展示项，清空主区
    async removeMeeting(meetingId) {
      await meetingsApi.deleteMeeting(meetingId)
      this.history = this.history.filter((m) => m.meeting_id !== meetingId)
      const wasCurrent = this.currentMeetingId === meetingId
      if (wasCurrent) this.clear()
      return { wasCurrent }
    },

    // RAG 追问（SSE 流式）：逐 token 填进 assistant 气泡
    async sendQuery(question) {
      if (!question.trim() || this.asking) return
      this.chatHistory.push({ role: 'user', content: question })
      // 占位 assistant 气泡，流式逐 token 累加
      const aiIdx = this.chatHistory.push({ role: 'assistant', content: '', sources: [] }) - 1
      this.asking = true
      const aiBubble = this.chatHistory[aiIdx]

      return chatApi.streamQuery(
        { sessionId: this.sessionId, question, meetingId: this.currentMeetingId || undefined },
        {
          onSources: (sources) => { aiBubble.sources = sources },
          onToken: (piece) => { aiBubble.content += piece },
          onDone: ({ answer }) => {
            // token 累加已基本完整，用 done 的 answer 兜底覆盖（防个别 chunk 丢失）
            if (answer && !aiBubble.content) aiBubble.content = answer
          },
          onError: (msg) => {
            aiBubble.content = `⚠️ ${msg}`
            aiBubble.sources = []
          },
          onFinally: () => { this.asking = false },
        },
      )
    },

    clearChat() {
      this.chatHistory = []
    },

    clear() {
      this.currentMeetingId = null
      this.currentMinutes = null
      this.currentMarkdown = ''
      this.clearChat()
    },
  },
})