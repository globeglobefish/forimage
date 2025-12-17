<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-card__header">
        <h1 class="auth-card__title">{{ $t('auth.resetPassword') }}</h1>
        <p class="auth-card__subtitle">{{ $t('auth.setNewPassword') }}</p>
      </div>
      
      <form v-if="!success" class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">{{ $t('auth.newPassword') }}</label>
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
              :class="{ 'is-error': form.password && passwordError }"
              :placeholder="$t('auth.newPasswordPlaceholder')"
              required
            />
            <button type="button" class="form-input-toggle" @click="showPassword = !showPassword">
              <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
          <span class="form-hint">{{ $t('auth.passwordRequirements') }}</span>
          <span v-if="form.password && passwordError" class="form-error">{{ passwordError }}</span>
        </div>
        
        <div class="form-group">
          <label class="form-label">{{ $t('auth.confirmPassword') }}</label>
          <div class="form-input-wrapper">
            <span class="form-input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </span>
            <input
              v-model="form.confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              class="form-input"
              :class="{ 'is-error': form.confirmPassword && confirmError }"
              :placeholder="$t('auth.confirmPasswordPlaceholder')"
              required
            />
          </div>
          <span v-if="form.confirmPassword && confirmError" class="form-error">{{ confirmError }}</span>
        </div>
        
        <button type="submit" class="btn btn--primary btn--lg btn--full" :disabled="loading || !isFormValid">
          <span v-if="loading" class="btn-loader"></span>
          {{ loading ? $t('common.loading') : $t('auth.resetPassword') }}
        </button>
      </form>
      
      <!-- Success State -->
      <div v-else class="success-box">
        <div class="success-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22,4 12,14.01 9,11.01"/>
          </svg>
        </div>
        <h3>{{ $t('auth.passwordResetSuccess') }}</h3>
        <p>{{ $t('auth.passwordResetSuccessHint') }}</p>
        <router-link to="/login">
          <button class="btn btn--primary btn--lg">{{ $t('auth.loginNow') }}</button>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const route = useRoute()
const loading = ref(false)
const success = ref(false)
const showPassword = ref(false)

const form = reactive({
  password: '',
  confirmPassword: '',
})

const passwordError = computed(() => {
  const p = form.password
  if (!p) return ''
  if (p.length < 8) return t('error.passwordTooShort')
  if (!/[a-z]/.test(p)) return t('error.passwordNeedsLower')
  if (!/[A-Z]/.test(p)) return t('error.passwordNeedsUpper')
  if (!/\d/.test(p)) return t('error.passwordNeedsDigit')
  return ''
})

const confirmError = computed(() => {
  if (!form.confirmPassword) return ''
  if (form.confirmPassword !== form.password) return t('error.passwordMismatch')
  return ''
})

const isFormValid = computed(() => {
  return form.password && !passwordError.value && form.confirmPassword && !confirmError.value
})

const handleSubmit = async () => {
  if (!isFormValid.value) return
  
  const token = route.query.token
  if (!token) {
    ElMessage.error(t('error.invalidResetLink'))
    return
  }
  
  loading.value = true
  try {
    await api.post('/auth/reset-password', {
      token,
      new_password: form.password,
    })
    success.value = true
  } catch (error) {
    const msg = error.response?.data?.detail || t('error.resetFailed')
    ElMessage.error(msg)
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
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}

.form-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

.form-error {
  font-size: 11px;
  color: var(--accent-danger);
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
  padding: 14px 40px 14px 44px;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-neu-pressed);
  transition: all var(--transition-fast);
  
  &::placeholder { color: var(--text-tertiary); }
  &:hover { background: var(--bg-tertiary); }
  &:focus {
    outline: none;
    background: var(--bg-card);
    border-color: var(--border-medium);
    box-shadow: var(--shadow-neu-flat);
  }
  &.is-error {
    border-color: var(--accent-danger);
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
  
  &:hover { color: var(--text-secondary); }
}

.success-box {
  text-align: center;
  padding: 20px 0;
  
  h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 12px;
  }
  
  p {
    font-size: 14px;
    color: var(--text-tertiary);
    margin: 0 0 24px;
  }
}

.success-icon {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  background: var(--accent-success-bg);
  border-radius: 50%;
  color: var(--accent-success);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    &:hover:not(:disabled) { opacity: 0.9; }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
  
  &--full { width: 100%; }
  &--lg { padding: 16px 32px; font-size: var(--text-base); }
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
