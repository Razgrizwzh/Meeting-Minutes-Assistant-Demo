import { defineStore } from 'pinia'
import * as meetingsApi from '@/api/meetings'

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
  }),

  getters: {
    hasMinutes: (state) => !!state.currentMinutes,
  },

  actions: {
    // 生成纪要：payload { text?, file?, meetingName?, date? }
    async generate(payload) {
      this.generating = true
      // 记录输入长度，用于进度条预估（文件按字节数近似为字符数）
      this.inputLength = payload.file ? payload.file.size || 0 : (payload.text || '').length
      try {
        const { data } = await meetingsApi.generateMeeting(payload)
        this.currentMeetingId = data.meeting_id
        this.currentMinutes = data.minutes
        this.currentMarkdown = data.markdown
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
      return data
    },

    clear() {
      this.currentMeetingId = null
      this.currentMinutes = null
      this.currentMarkdown = ''
    },
  },
})
