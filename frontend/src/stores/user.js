import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)
  const loaded = ref(false)

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(accessToken, refresh) {
    token.value = accessToken
    refreshToken.value = refresh
    localStorage.setItem('token', accessToken)
    localStorage.setItem('refreshToken', refresh)
  }

  function clearTokens() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  async function loadUser() {
    if (!token.value) {
      loaded.value = true
      return
    }

    try {
      const response = await api.get('/user/me')
      user.value = response.data
    } catch (error) {
      clearTokens()
    } finally {
      loaded.value = true
    }
  }

  async function login(username, password) {
    const response = await api.post('/auth/login', { username, password })
    setTokens(response.data.access_token, response.data.refresh_token)
    await loadUser()
    return response.data
  }

  async function register(username, email, password) {
    const response = await api.post('/auth/register', { username, email, password })
    return response.data
  }

  async function logout() {
    clearTokens()
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token')
    }

    try {
      const response = await api.post('/auth/refresh', null, {
        headers: { Authorization: `Bearer ${refreshToken.value}` }
      })
      setTokens(response.data.access_token, response.data.refresh_token)
      return response.data.access_token
    } catch (error) {
      clearTokens()
      throw error
    }
  }

  return {
    user,
    token,
    refreshToken,
    loaded,
    isLoggedIn,
    isAdmin,
    setTokens,
    clearTokens,
    loadUser,
    login,
    register,
    logout,
    refreshAccessToken,
  }
})
