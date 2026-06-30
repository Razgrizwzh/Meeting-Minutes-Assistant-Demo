import http from './index'

// 发起追问：payload { sessionId, question, meetingId? }
// 后端 ChatQueryIn 期望 snake_case（session_id/question/meeting_id），
// 此处做一次映射，避免 422 Unprocessable Content。
export const query = (payload) =>
  http.post('/chat/query', {
    session_id: payload.sessionId,
    question: payload.question,
    meeting_id: payload.meetingId,
  })