<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-card__header">
        <h1 class="auth-card__title">{{ $t('auth.forgotPassword') }}</h1>
        <p class="auth-card__subtitle">{{ $t('auth.resetPasswordHint') }}</p>
      </div>
      
      <form v-if="!sent" class="auth-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">{{ $t('auth.email') }}</label>
          <div class="form-input-wrapper">
            <span class="form-input-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </span>
            <input
              v-model="email"
              type="email"
              class="form-input"
              :placeholder="$t('auth.emailPlaceholder')"
              required
            />
          </div>
        </div>
        
        <!-- Captcha -->
        <div class="form-group">
          <label class="form-label">{{ $t('auth.captcha') }}</label>
          <div class="captcha-row">
            <div class="form-input-wrapper captcha-input-wrapper">
              <input
                v-model="captchaCode"
                type="text"
                class="form-input"
                :placeholder="$t('auth.captchaPlaceholder')"
                maxlength="4"
                @input="captchaCode = captchaCode.toUpperCase()"
              />
            </div>
            <div class="captcha-image" @click="refreshCaptcha" :title="$t('auth.refreshCaptcha')">
              <img v-if="captchaImage" :src="captchaImage" :alt="$t('auth.captcha')" />
              <span v-else class="captcha-loading">{{ $t('common.loading') }}</span>
            </div>
          </div>
          <span class="form-hint">{{ $t('auth.refreshCaptcha') }}</span>
        </div>
        
        <button type="submit" class="btn btn--primary btn--lg btn--full" :disabled="loading || !email || !captchaCode || captchaCode.length !== 4">
          <span v-if="loading" class="btn-loader"></span>
          {{ loading ? $t('common.loading') : $t('auth.sendResetLink') }}
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
        <h3>{{ $t('auth.emailSent') }}</h3>
        <p>{{ $t('auth.emailSentHint') }}</p>
      </div>
      
      <div class="auth-card__footer">
        <router-link to="/login" class="auth-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          {{ $t('auth.backToLogin') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const email = ref('')
const loading = ref(false)
const sent = ref(false)
const captchaImage = ref('')
const captchaId = ref('')
const captchaCode = ref('')

const refreshCaptcha = async () => {
  try {
    const response = await api.get('/auth/captcha')
    captchaId.value = response.data.captcha_id
    captchaImage.value = response.data.image
    captchaCode.value = ''
  } catch (error) {
    console.error('Failed to load captcha:', error)
  }
}

onMounted(() => {
  refreshCaptcha()
})

const handleSubmit = async () => {
  if (!email.value || !captchaCode.value || captchaCode.value.length !== 4) return
  
  loading.value = true
  try {
    await api.post('/auth/forgot-password', { 
      email: email.value,
      captcha_id: captchaId.value,
      captcha_code: captchaCode.value
    })
    sent.value = true
  } catch (error) {
    const detail = error.response?.data?.detail || ''
    if (detail.includes('验证码') || detail.includes('captcha')) {
      ElMessage.error(t('error.invalidCaptcha'))
      refreshCaptcha()
    } else if (detail.includes('频繁') || detail.includes('rate')) {
      ElMessage.error(t('error.tooManyRequests'))
    } else {
      // Still show success to prevent email enumeration
      sent.value = true
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
  
  &::placeholder { color: var(--text-tertiary); }
  &:hover { background: var(--bg-tertiary); }
  &:focus {
    outline: none;
    background: var(--bg-card);
    border-color: var(--border-medium);
    box-shadow: var(--shadow-neu-flat);
  }
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
    line-height: 1.6;
    margin: 0;
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

.auth-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
  
  &:hover { color: var(--text-primary); }
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

// Captcha
.captcha-row {
  display: flex;
  gap: 12px;
  align-items: stretch;
}

.captcha-input-wrapper {
  flex: 1;
  
  .form-input {
    padding-left: 14px;
  }
}

.captcha-image {
  width: 120px;
  height: 48px;
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  &:hover {
    opacity: 0.8;
  }
}

.captcha-loading {
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
</style>
