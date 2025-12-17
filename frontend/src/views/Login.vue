<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-card__header">
        <h1 class="auth-card__title">{{ $t('auth.welcomeBack') }}</h1>
        <p class="auth-card__subtitle">{{ $t('auth.loginToContinue') }}</p>
      </div>
      
      <form class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">{{ $t('auth.usernameOrEmail') }}</label>
          <div class="form-input-wrapper">
            <span class="form-input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </span>
            <input
              v-model="form.username"
              type="text"
              class="form-input"
              :placeholder="$t('auth.usernameOrEmail')"
              required
            />
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label">{{ $t('auth.password') }}</label>
          <div class="form-input-wrapper">
            <span class="form-input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </span>
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              :placeholder="$t('auth.password')"
              required
            />
            <button
              type="button"
              class="form-input-toggle"
              @click="showPassword = !showPassword"
            >
              <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Error Message -->
        <div v-if="errorMessage" class="form-error-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {{ errorMessage }}
        </div>
        
        <div class="form-group">
          <button type="submit" class="btn btn--primary btn--lg btn--full" :disabled="loading">
            <span v-if="loading" class="btn-loader"></span>
            <span v-else>{{ $t('auth.login') }}</span>
          </button>
        </div>
      </form>
      
      <div class="auth-card__footer">
        <router-link to="/forgot-password" class="auth-link">{{ $t('auth.forgotPassword') }}</router-link>
        <span class="auth-divider">·</span>
        <router-link to="/register" class="auth-link">{{ $t('auth.register') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const showPassword = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const errorMessage = ref('')

const handleSubmit = async () => {
  errorMessage.value = ''
  
  if (!form.username.trim()) {
    errorMessage.value = t('error.fieldRequired')
    return
  }
  
  if (!form.password) {
    errorMessage.value = t('error.fieldRequired')
    return
  }
  
  loading.value = true
  try {
    await userStore.login(form.username.trim(), form.password)
    ElMessage.success(t('auth.loginSuccess'))
    
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    const detail = error.response?.data?.detail || ''
    if (detail.includes('password') || detail.includes('username')) {
      errorMessage.value = t('error.invalidCredentials')
    } else if (detail.includes('verified')) {
      errorMessage.value = t('error.emailNotVerified')
    } else if (detail.includes('disabled')) {
      errorMessage.value = t('error.accountDisabled')
    } else if (detail.includes('locked')) {
      errorMessage.value = t('error.accountLocked')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 280px);
  padding: 40px 0;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 40px;
  box-shadow: var(--shadow-neu-flat);
  
  &__header {
    text-align: center;
    margin-bottom: 32px;
  }
  
  &__title {
    font-size: var(--text-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  
  &__subtitle {
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }
  
  &__footer {
    text-align: center;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--border-light);
  }
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}

.form-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input-icon {
  position: absolute;
  left: 14px;
  color: var(--text-tertiary);
  pointer-events: none;
  display: flex;
}

.form-input {
  width: 100%;
  padding: 14px 14px 14px 44px;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-neu-pressed);
  transition: all var(--transition-fast);
  
  &::placeholder {
    color: var(--text-tertiary);
  }
  
  &:hover {
    background: var(--bg-tertiary);
  }
  
  &:focus {
    outline: none;
    background: var(--bg-card);
    border-color: var(--border-medium);
    box-shadow: var(--shadow-neu-flat);
  }
}

.form-input-toggle {
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  padding: 4px;
  
  &:hover {
    color: var(--text-secondary);
  }
}

.auth-link {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
  
  &:hover {
    color: var(--text-primary);
  }
}

.auth-divider {
  margin: 0 12px;
  color: var(--border-medium);
}

.form-error-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--accent-danger-bg);
  color: var(--accent-danger);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  
  svg {
    flex-shrink: 0;
  }
}

.btn {
  &--full {
    width: 100%;
  }
  
  &--lg {
    padding: 16px 32px;
    font-size: var(--text-base);
  }
}

.btn-loader {
  width: 18px;
  height: 18px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
