import http from './index'

// 注册（后端注册即登录，返回 TokenOut）
export const register = (username, password) =>
  http.post('/auth/register', { username, password })

export const login = (username, password) =>
  http.post('/auth/login', { username, password })

// 登出（后端无状态空操作，真实登出是前端清 token）
export const logout = () => http.post('/auth/logout')
