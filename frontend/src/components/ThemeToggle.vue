<template>
  <button 
    class="theme-toggle" 
    :class="{ 'is-dark': themeStore.isDark }"
    @click="themeStore.toggleTheme"
    :title="themeStore.isDark ? $t('theme.light') : $t('theme.dark')"
  >
    <span class="toggle-track">
      <span class="toggle-thumb"></span>
      <span class="toggle-icon toggle-icon--sun">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" stroke-width="2" fill="none"/>
        </svg>
      </span>
      <span class="toggle-icon toggle-icon--moon">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </span>
    </span>
  </button>
</template>

<script setup>
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
</script>

<style lang="scss" scoped>
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  margin: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  vertical-align: middle;
  box-sizing: border-box;
  line-height: 1;
  
  &:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
  }
  
  &:focus {
    outline: none;
  }
}

.toggle-track {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
}

.toggle-icon {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &--sun {
    color: #f59e0b;
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
  
  &--moon {
    color: #a78bfa;
    opacity: 0;
    transform: scale(0.5) rotate(-90deg);
  }
}

.theme-toggle.is-dark {
  .toggle-icon--sun {
    opacity: 0;
    transform: scale(0.5) rotate(90deg);
  }
  
  .toggle-icon--moon {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

.toggle-thumb {
  display: none;
}
</style>
