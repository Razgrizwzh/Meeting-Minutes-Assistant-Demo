import http from './index'

// 生成会议纪要：用 FormData 支持「粘贴文本」或「上传文件」两种方式。
// payload: { text?, file?, meetingName?, date? }
export const generateMeeting = (payload) => {
  const fd = new FormData()
  if (payload.file) {
    fd.append('file', payload.file)
  } else if (payload.text) {
    fd.append('text', payload.text)
  }
  if (payload.meetingName) fd.append('meeting_name', payload.meetingName)
  if (payload.date) fd.append('date', payload.date)
  return http.post('/meetings/generate', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    // 纪要生成长文本可能耗时 60-90 秒（qwen3.7-plus 实测 1280 字 ~54s），
    // 远超全局 30s 超时；此处单独放宽到 180s，避免前端误报"生成失败"
    // 而后端其实仍在跑并已保存历史。
    timeout: 180000,
  })
}

// 历史会议列表（需登录）
export const listHistory = () => http.get('/meetings/history')

// 会议详情
export const getMeeting = (meetingId) => http.get(`/meetings/${meetingId}`)
