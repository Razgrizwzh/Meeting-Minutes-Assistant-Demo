import http from './index'

// 发起追问（后续轮实现 RAG；本轮后端返回 501）
export const query = (payload) => http.post('/chat/query', payload)
