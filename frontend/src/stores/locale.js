import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { SUPPORTED_LOCALES, setLocale as setI18nLocale, getLocale } from '@/locales'

export const useLocaleStore = defineStore('locale', () => {
  // 当前语言
  const currentLocale = ref(getLocale())
  
  // 支持的语言列表
  const supportedLocales = SUPPORTED_LOCALES
  
  // 当前语言信息
  const currentLocaleInfo = computed(() => {
    return supportedLocales.find(l => l.code === currentLocale.value) || supportedLocales[0]
  })
  
  // 切换语言
  const switchLocale = (locale) => {
    if (setI18nLocale(locale)) {
      currentLocale.value = locale
      return true
    }
    return false
  }
  
  // 初始化
  const initLocale = () => {
    document.documentElement.lang = currentLocale.value
  }
  
  return {
    currentLocale,
    supportedLocales,
    currentLocaleInfo,
    switchLocale,
    initLocale,
  }
})
