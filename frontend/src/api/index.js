import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    const requestUrl = originalRequest?.url || ''

    // Skip token refresh for auth endpoints (login, register, etc.)
    const isAuthEndpoint = requestUrl.includes('/auth/')

    // Handle 401 errors (token expired) - but NOT for auth endpoints
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true

      try {
        const userStore = useUserStore()
        const newToken = await userStore.refreshAccessToken()
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        const userStore = useUserStore()
        userStore.clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Translate common error messages to Chinese
    let message = error.response?.data?.detail || error.message || '请求失败'
    
    // Common error translations
    const errorTranslations = {
      'Incorrect username or password': '用户名或密码错误',
      'User not found': '用户不存在',
      'User not found or inactive': '用户不存在或已禁用',
      'Email not verified': '邮箱未验证，请先验证邮箱',
      'Please verify your email first': '请先验证您的邮箱',
      'Account is disabled': '账号已被禁用',
      'Your account has been disabled': '您的账号已被禁用',
      'Account is locked': '账号已被锁定，请稍后再试',
      'Account is temporarily locked': '账号已被临时锁定',
      'Invalid token': '无效的令牌',
      'Invalid refresh token': '无效的刷新令牌',
      'Invalid verification token': '无效的验证链接',
      'Verification token has expired': '验证链接已过期',
      'Invalid reset token': '无效的重置链接',
      'Reset token has expired': '重置链接已过期',
      'Token expired': '令牌已过期',
      'Not authenticated': '请先登录',
      'Not enough permissions': '权限不足',
      'Too many failed login attempts. Please try again later.': '登录尝试次数过多，请稍后再试',
      'Rate limit exceeded': '请求过于频繁，请稍后再试',
      'File too large': '文件太大',
      'Invalid file type': '不支持的文件类型',
      'Network Error': '网络错误，请检查网络连接',
      'Username already registered': '该用户名已被注册',
      'Email already registered': '该邮箱已被注册',
      'Image not found': '图片不存在',
      'Album not found': '相册不存在',
      'Permission denied': '没有权限执行此操作',
    }
    
    if (errorTranslations[message]) {
      message = errorTranslations[message]
    }
    
    // Don't show error for site settings (it's optional, uses defaults on failure)
    if (!requestUrl.includes('/site/settings')) {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default api
