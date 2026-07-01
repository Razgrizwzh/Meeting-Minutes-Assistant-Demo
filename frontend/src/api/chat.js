import http from './index'

const TOKEN_KEY = 'ma_token'

// 发起追问：payload { sessionId, question, meetingId? }
// 后端 ChatQueryIn 期望 snake_case（session_id/question/meeting_id），
// 此处做一次映射，避免 422 Unprocessable Content。
export const query = (payload) =>
  http.post('/chat/query', {
    session_id: payload.sessionId,
    question: payload.question,
    meeting_id: payload.meetingId,
  })

// 取某会议持久化的对话记录（需登录）：{ messages: [{role, content, sources}] }
export const getHistory = (meetingId) => http.get(`/chat/${meetingId}`)

/**
 * SSE 流式追问。
 * @param {Object} payload { sessionId, question, meetingId? }
 * @param {Object} handlers { onSources(sources), onToken(text), onDone({answer,sources}), onError(msg), onFinally() }
 *
 * 用原生 fetch + ReadableStream 解析 SSE（axios 不便处理流）；
 * JWT 手动从 localStorage 取并附 Authorization 头。
 * 返回一个 { cancel } 句柄，可用于中止（如切走 Tab）。
 */
export function streamQuery(payload, handlers) {
  const { onSources, onToken, onDone, onError, onFinally } = handlers || {}
  const controller = new AbortController()

  ;(async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY)
      const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          session_id: payload.sessionId,
          question: payload.question,
          meeting_id: payload.meetingId,
        }),
        signal: controller.signal,
      })

      if (!resp.ok || !resp.body) {
        // 非 2xx：尝试读 detail
        let msg = '追问失败，请重试'
        try {
          const data = await resp.json()
          const raw = data.detail
          msg = Array.isArray(raw) ? raw[0]?.msg : raw || msg
        } catch { /* ignore */ }
        if (resp.status === 401) {
          // 触发与 axios 拦截器一致的登出事件
          localStorage.removeItem(TOKEN_KEY)
          localStorage.removeItem('ma_user')
          window.dispatchEvent(new CustomEvent('auth:logout'))
          msg = '登录已过期，请重新登录'
        }
        onError && onError(msg)
        onFinally && onFinally()
        return
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      // SSE 以空行分隔事件块；逐块解析 event:/data:
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        // 按双换行切块（SSE 事件边界）
        let idx
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const block = buffer.slice(0, idx)
          buffer = buffer.slice(idx + 2)
          const event = _parseSSEBlock(block)
          if (!event) continue
          if (event.event === 'sources') onSources && onSources(event.data.sources || [])
          else if (event.event === 'token') onToken && onToken(event.data.content || '')
          else if (event.event === 'done') {
            onDone && onDone({ answer: event.data.answer, sources: event.data.sources || [] })
            onFinally && onFinally()
            return
          } else if (event.event === 'error') {
            onError && onError(event.data.message || '追问失败，请重试')
            onFinally && onFinally()
            return
          }
        }
      }
      // 流自然结束但没收到 done：按结束处理
      onFinally && onFinally()
    } catch (e) {
      if (e.name === 'AbortError') return // 主动取消，不打扰
      onError && onError('网络异常，请重试')
      onFinally && onFinally()
    }
  })()

  return { cancel: () => controller.abort() }
}

function _parseSSEBlock(block) {
  // 一个 SSE 块由若干行组成：event: xxx / data: {...}
  let event = 'message'
  const dataLines = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  if (!dataLines.length) return null
  try {
    return { event, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    return null
  }
}