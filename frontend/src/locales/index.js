import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.js'
import zhTW from './zh-TW.js'
import en from './en.js'

// 支持的语言列表
export const SUPPORTED_LOCALES = [
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'zh-TW', name: '繁體中文', flag: 'HK' },
  { code: 'en', name: 'English', flag: 'UK' },
]

// 获取默认语言
function getDefaultLocale() {
  // 1. 优先从 localStorage 读取
  const savedLocale = localStorage.getItem('locale')
  if (savedLocale && SUPPORTED_LOCALES.some(l => l.code === savedLocale)) {
    return savedLocale
  }
  
  // 2. 从浏览器语言检测
  const browserLang = navigator.language || navigator.userLanguage
  
  // 精确匹配
  if (SUPPORTED_LOCALES.some(l => l.code === browserLang)) {
    return browserLang
  }
  
  // 模糊匹配 (zh -> zh-CN, en-US -> en)
  const langPrefix = browserLang.split('-')[0]
  if (langPrefix === 'zh') {
    // 繁体中文地区
    if (['zh-TW', 'zh-HK', 'zh-MO'].includes(browserLang)) {
      return 'zh-TW'
    }
    return 'zh-CN'
  }
  if (langPrefix === 'en') {
    return 'en'
  }
  
  // 3. 默认简体中文
  return 'zh-CN'
}

// 创建 i18n 实例
const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: getDefaultLocale(),
  fallbackLocale: 'zh-CN', // 回退语言
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en': en,
  },
  // 缺失翻译时的警告
  missingWarn: import.meta.env.DEV,
  fallbackWarn: import.meta.env.DEV,
})

// 切换语言
export function setLocale(locale) {
  if (SUPPORTED_LOCALES.some(l => l.code === locale)) {
    i18n.global.locale.value = locale
    localStorage.setItem('locale', locale)
    document.documentElement.lang = locale
    return true
  }
  return false
}

// 获取当前语言
export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
