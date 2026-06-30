import http from './index'

// 生成会议纪要：用 FormData 支持「粘贴文本」或「上传文件」两种方式。
// payload: { text?, file?, meetingName?, date?, sessionId? }
export const generateMeeting = (payload) => {
  const fd = new FormData()
  if (payload.file) {
    fd.append('file', payload.file)
  } else if (payload.text) {
    fd.append('text', payload.text)
  }
  if (payload.meetingName) fd.append('meeting_name', payload.meetingName)
  if (payload.date) fd.append('date', payload.date)
  if (payload.sessionId) fd.append('session_id', payload.sessionId)
  return http.post('/meetings/generate', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    // 纪要生成长文本耗时较长；放宽到 180s 避免前端误报"生成失败"
    timeout: 180000,
  })
}

// 历史会议列表（需登录）
export const listHistory = () => http.get('/meetings/history')

// 会议详情
export const getMeeting = (meetingId) => http.get(`/meetings/${meetingId}`)

// 导出（返回 Blob）：format = 'md' | 'docx'
export const exportMeeting = (meetingId, format) =>
  http.get(`/meetings/${meetingId}/export`, {
    params: { format },
    responseType: 'blob',
  })