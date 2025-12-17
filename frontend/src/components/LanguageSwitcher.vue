<template>
  <div class="lang-switcher" ref="switcherRef">
    <button 
      class="lang-btn" 
      @click="toggleDropdown"
      :title="$t('language.switchLanguage')"
    >
      <svg class="lang-btn__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="2" y1="12" x2="22" y2="12"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
      </svg>
      <span class="lang-btn__text">{{ currentShortCode }}</span>
      <svg class="lang-btn__arrow" :class="{ 'is-open': isOpen }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="6,9 12,15 18,9"/>
      </svg>
    </button>
    
    <transition name="dropdown">
      <div v-if="isOpen" class="lang-dropdown">
        <button
          v-for="locale in locales"
          :key="locale.code"
          class="lang-option"
          :class="{ 'is-active': locale.code === currentLocale }"
          @click="selectLocale(locale.code)"
        >
          <span class="lang-option__name">{{ locale.name }}</span>
          <svg v-if="locale.code === currentLocale" class="lang-option__check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20,6 9,17 4,12"/>
          </svg>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useLocaleStore } from '@/stores/locale'
import { ElMessage } from 'element-plus'

const localeStore = useLocaleStore()
const switcherRef = ref(null)
const isOpen = ref(false)

const locales = [
  { code: 'zh-CN', name: '简体中文', short: '中' },
  { code: 'zh-TW', name: '繁體中文', short: '繁' },
  { code: 'en', name: 'English', short: 'EN' },
]

const currentLocale = computed(() => localeStore.currentLocale)

const currentShortCode = computed(() => {
  const locale = locales.find(l => l.code === currentLocale.value)
  return locale ? locale.short : '中'
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectLocale = (code) => {
  if (code !== currentLocale.value) {
    localeStore.switchLocale(code)
    const locale = locales.find(l => l.code === code)
    if (locale) {
      ElMessage.success(locale.name)
    }
  }
  isOpen.value = false
}

const handleClickOutside = (event) => {
  if (switcherRef.value && !switcherRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style lang="scss" scoped>
.lang-switcher {
  position: relative;
  display: inline-flex;
  align-items: center;
  height: 36px;
}

.lang-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
  height: 36px;
  margin: 0;
  vertical-align: middle;
  box-sizing: border-box;
  line-height: 1;
  
  &:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
  }
  
  &__icon {
    color: var(--text-tertiary);
    flex-shrink: 0;
    display: flex;
    align-items: center;
  }
  
  &__text {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    min-width: 20px;
    text-align: center;
    line-height: 1;
  }
  
  &__arrow {
    color: var(--text-tertiary);
    transition: transform 0.2s ease;
    flex-shrink: 0;
    margin-left: 2px;
    display: flex;
    align-items: center;
    
    &.is-open {
      transform: rotate(180deg);
    }
  }
}

.lang-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 140px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  padding: 4px;
  z-index: 1000;
}

.lang-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
  
  &:hover {
    background: var(--bg-secondary);
  }
  
  &.is-active {
    .lang-option__name {
      color: var(--accent-primary);
      font-weight: 600;
    }
  }
  
  &__name {
    font-size: 13px;
    color: var(--text-primary);
    font-weight: 500;
  }
  
  &__check {
    color: var(--accent-primary);
    flex-shrink: 0;
  }
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
