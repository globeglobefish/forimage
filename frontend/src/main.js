import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// Element Plus 多语言支持
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import zhTw from 'element-plus/es/locale/lang/zh-tw'
import en from 'element-plus/es/locale/lang/en'
import App from './App.vue'
import router from './router'
import i18n, { getLocale } from './locales'
import './styles/variables.scss'
import './styles/main.scss'

// Element Plus 语言映射
const elementLocales = {
  'zh-CN': zhCn,
  'zh-TW': zhTw,
  'en': en,
}

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(ElementPlus, {
  locale: elementLocales[getLocale()] || zhCn,
})

app.mount('#app')
