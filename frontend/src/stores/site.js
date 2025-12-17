import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import api from '@/api'

export const useSiteStore = defineStore('site', () => {
  const settings = ref({
    site_name: 'Forimage',
    site_title: 'Forimage - 简洁优雅的图床服务',
    site_description: '免费稳定的图片托管服务',
    site_slogan: '简洁优雅的图床服务',
    site_footer: 'Forimage - 让图片分享更简单',
    site_logo: '',
    site_logo_dark: '',
    site_favicon: '',
    timezone: 'Asia/Shanghai',
    max_upload_size_guest: 5242880,
    max_upload_size_user: 10485760,
    allowed_extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'],
    enable_registration: true,
    enable_guest_upload: true,
    guest_rate_limit_per_minute: 3,
    guest_rate_limit_per_hour: 10,
    guest_rate_limit_per_day: 30,
    user_rate_limit_per_minute: 10,
    user_rate_limit_per_hour: 100,
    user_rate_limit_per_day: 500,
  })
  
  const loaded = ref(false)
  const loading = ref(false)

  const loadSettings = async () => {
    if (loading.value) return
    
    loading.value = true
    try {
      const response = await api.get('/site/settings')
      settings.value = response.data
      loaded.value = true
      // Update page title and meta
      updatePageMeta()
    } catch (error) {
      console.error('Failed to load site settings:', error)
    } finally {
      loading.value = false
    }
  }

  // Update page title, description and favicon
  const updatePageMeta = () => {
    // Update title
    document.title = settings.value.site_title || settings.value.site_name
    
    // Update meta description
    let metaDesc = document.querySelector('meta[name="description"]')
    if (!metaDesc) {
      metaDesc = document.createElement('meta')
      metaDesc.name = 'description'
      document.head.appendChild(metaDesc)
    }
    metaDesc.content = settings.value.site_description || ''
    
    // Update favicon
    if (settings.value.site_favicon) {
      let favicon = document.querySelector('link[rel="icon"]')
      if (!favicon) {
        favicon = document.createElement('link')
        favicon.rel = 'icon'
        document.head.appendChild(favicon)
      }
      favicon.href = settings.value.site_favicon
    }
  }

  // Computed helpers
  const siteName = () => settings.value.site_name
  const siteTitle = () => settings.value.site_title
  const siteDescription = () => settings.value.site_description
  const siteSlogan = () => settings.value.site_slogan
  const siteFooter = () => settings.value.site_footer
  const siteLogo = () => settings.value.site_logo
  const siteLogoDark = () => settings.value.site_logo_dark
  const siteFavicon = () => settings.value.site_favicon
  const maxSizeGuest = () => settings.value.max_upload_size_guest
  const maxSizeUser = () => settings.value.max_upload_size_user
  const maxSizeGuestMB = () => Math.round(settings.value.max_upload_size_guest / 1024 / 1024)
  const maxSizeUserMB = () => Math.round(settings.value.max_upload_size_user / 1024 / 1024)
  const allowedExtensions = () => settings.value.allowed_extensions
  const isRegistrationEnabled = () => settings.value.enable_registration
  const isGuestUploadEnabled = () => settings.value.enable_guest_upload
  
  const timezone = () => settings.value.timezone || 'Asia/Shanghai'
  const guestRateLimitPerMinute = () => settings.value.guest_rate_limit_per_minute
  const guestRateLimitPerHour = () => settings.value.guest_rate_limit_per_hour
  const guestRateLimitPerDay = () => settings.value.guest_rate_limit_per_day
  const userRateLimitPerMinute = () => settings.value.user_rate_limit_per_minute
  const userRateLimitPerHour = () => settings.value.user_rate_limit_per_hour
  const userRateLimitPerDay = () => settings.value.user_rate_limit_per_day

  return {
    settings,
    loaded,
    loading,
    loadSettings,
    updatePageMeta,
    siteName,
    siteTitle,
    siteDescription,
    siteSlogan,
    siteFooter,
    siteLogo,
    siteLogoDark,
    siteFavicon,
    maxSizeGuest,
    maxSizeUser,
    maxSizeGuestMB,
    maxSizeUserMB,
    allowedExtensions,
    isRegistrationEnabled,
    isGuestUploadEnabled,
    timezone,
    guestRateLimitPerMinute,
    guestRateLimitPerHour,
    guestRateLimitPerDay,
    userRateLimitPerMinute,
    userRateLimitPerHour,
    userRateLimitPerDay,
  }
})
