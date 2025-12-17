<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-card__header">
        <h1 class="auth-card__title">{{ $t('auth.createAccount') }}</h1>
        <p class="auth-card__subtitle">{{ $t('auth.registerToContinue') }}</p>
      </div>
      
      <form class="auth-form" @submit.prevent="handleSubmit">
        <!-- Username -->
        <div class="form-group">
          <label class="form-label">{{ $t('auth.username') }}</label>
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
              :class="{ 'is-error': form.username && usernameError }"
              :placeholder="$t('auth.username')"
              @blur="validateUsername"
            />
            <span v-if="form.username && !usernameError" class="form-input-check">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20,6 9,17 4,12"/>
              </svg>
            </span>
          </div>
          <span class="form-hint">{{ $t('error.invalidUsername') }}</span>
          <span v-if="form.username && usernameError" class="form-error">{{ usernameError }}</span>
        </div>
        
        <!-- Email -->
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
              v-model="form.email"
              type="email"
              class="form-input"
              :class="{ 'is-error': form.email && emailError }"
              :placeholder="$t('auth.email')"
              @blur="validateEmail"
            />
            <span v-if="form.email && !emailError" class="form-input-check">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20,6 9,17 4,12"/>
              </svg>
            </span>
          </div>
          <span class="form-hint">{{ $t('auth.verifyEmailHint') }}</span>
          <span v-if="form.email && emailError" class="form-error">{{ emailError }}</span>
        </div>
        
        <!-- Password -->
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
              @input="validatePassword"
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
          <!-- Password Requirements -->
          <div class="password-requirements" v-if="form.password">
            <div class="password-requirements__header">
              <span>{{ $t('auth.password') }}</span>
              <span class="password-strength-text" :class="passwordStrengthClass">{{ passwordStrengthText }}</span>
            </div>
            <div class="password-requirements__bar">
              <div 
                class="password-requirements__fill"
                :class="passwordStrengthClass"
                :style="{ width: passwordStrength + '%' }"
              />
            </div>
            <div class="password-requirements__list">
              <div class="requirement" :class="{ 'is-met': passwordChecks.length }">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline v-if="passwordChecks.length" points="20,6 9,17 4,12"/>
                  <circle v-else cx="12" cy="12" r="10" stroke-width="2"/>
                </svg>
                {{ $t('error.passwordTooShort') }}
              </div>
              <div class="requirement" :class="{ 'is-met': passwordChecks.lowercase }">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline v-if="passwordChecks.lowercase" points="20,6 9,17 4,12"/>
                  <circle v-else cx="12" cy="12" r="10" stroke-width="2"/>
                </svg>
                {{ $t('error.passwordNeedsLower') }}
              </div>
              <div class="requirement" :class="{ 'is-met': passwordChecks.uppercase }">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline v-if="passwordChecks.uppercase" points="20,6 9,17 4,12"/>
                  <circle v-else cx="12" cy="12" r="10" stroke-width="2"/>
                </svg>
                {{ $t('error.passwordNeedsUpper') }}
              </div>
              <div class="requirement" :class="{ 'is-met': passwordChecks.number }">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <polyline v-if="passwordChecks.number" points="20,6 9,17 4,12"/>
                  <circle v-else cx="12" cy="12" r="10" stroke-width="2"/>
                </svg>
                {{ $t('error.passwordNeedsDigit') }}
              </div>
            </div>
          </div>
          <span v-else class="form-hint">{{ $t('error.passwordTooShort') }}</span>
        </div>
        
        <!-- Confirm Password -->
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
              :class="{ 'is-error': form.confirmPassword && confirmPasswordError }"
              :placeholder="$t('auth.confirmPassword')"
            />
            <span v-if="form.confirmPassword && !confirmPasswordError" class="form-input-check">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20,6 9,17 4,12"/>
              </svg>
            </span>
          </div>
          <span v-if="form.confirmPassword && confirmPasswordError" class="form-error">{{ confirmPasswordError }}</span>
        </div>
        
        <!-- Captcha -->
        <div class="form-group">
          <label class="form-label">{{ $t('auth.captcha') }}</label>
          <div class="captcha-row">
            <div class="form-input-wrapper captcha-input-wrapper">
              <span class="form-input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                </svg>
              </span>
              <input
                v-model="form.captchaCode"
                type="text"
                class="form-input"
                :class="{ 'is-error': form.captchaCode && captchaError }"
                :placeholder="$t('auth.captchaPlaceholder')"
                maxlength="4"
                @input="form.captchaCode = form.captchaCode.toUpperCase()"
              />
            </div>
            <div class="captcha-image" @click="refreshCaptcha" :title="$t('auth.refreshCaptcha')">
              <img v-if="captchaImage" :src="captchaImage" :alt="$t('auth.captcha')" />
              <span v-else class="captcha-loading">{{ $t('common.loading') }}</span>
            </div>
          </div>
          <span class="form-hint">{{ $t('auth.refreshCaptcha') }}</span>
          <span v-if="form.captchaCode && captchaError" class="form-error">{{ captchaError }}</span>
        </div>
        
        <!-- Submit -->
        <div class="form-group">
          <button 
            type="submit" 
            class="btn btn--primary btn--lg btn--full" 
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="btn-loader"></span>
            <span v-else>{{ $t('auth.register') }}</span>
          </button>
          <p v-if="!isFormValid && hasInteracted" class="form-summary-error">
            {{ formSummaryError }}
          </p>
        </div>
      </form>
      
      <div class="auth-card__footer">
        {{ $t('auth.alreadyHaveAccount') }}
        <router-link to="/login" class="auth-link">{{ $t('auth.login') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const siteStore = useSiteStore()



const loading = ref(false)
const showPassword = ref(false)
const hasInteracted = ref(false)
const captchaImage = ref('')
const captchaId = ref('')

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  captchaCode: '',
})

// Load captcha on mount
const refreshCaptcha = async () => {
  try {
    const response = await api.get('/auth/captcha')
    captchaId.value = response.data.captcha_id
    captchaImage.value = response.data.image
    form.captchaCode = ''
  } catch (error) {
    console.error('Failed to load captcha:', error)
  }
}

onMounted(() => {
  if (!siteStore.isRegistrationEnabled()) {
    ElMessage.warning(t('error.registrationDisabled'))
    router.push('/login')
  } else {
    refreshCaptcha()
  }
})

// Username validation
const usernameError = computed(() => {
  if (!form.username) return ''
  if (form.username.length < 3) return t('error.usernameTooShort')
  if (form.username.length > 20) return t('error.usernameTooLong')
  if (!/^[a-zA-Z0-9_]+$/.test(form.username)) return t('error.invalidUsername')
  if (/^\d/.test(form.username)) return t('error.usernameStartsWithDigit')
  return ''
})

const validateUsername = () => {
  hasInteracted.value = true
}

// Email validation
const emailError = computed(() => {
  if (!form.email) return ''
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(form.email)) return t('error.invalidEmail')
  return ''
})

const validateEmail = () => {
  hasInteracted.value = true
}

// Password validation
const passwordChecks = computed(() => ({
  length: form.password.length >= 8,
  lowercase: /[a-z]/.test(form.password),
  uppercase: /[A-Z]/.test(form.password),
  number: /\d/.test(form.password),
}))

const passwordStrength = computed(() => {
  const checks = passwordChecks.value
  let strength = 0
  if (checks.length) strength += 25
  if (checks.lowercase) strength += 25
  if (checks.uppercase) strength += 25
  if (checks.number) strength += 25
  return strength
})

const passwordStrengthClass = computed(() => {
  if (passwordStrength.value <= 25) return 'is-weak'
  if (passwordStrength.value <= 50) return 'is-fair'
  if (passwordStrength.value <= 75) return 'is-good'
  return 'is-strong'
})

const passwordStrengthText = computed(() => {
  if (passwordStrength.value <= 25) return t('auth.passwordWeak')
  if (passwordStrength.value <= 50) return t('auth.passwordFair')
  if (passwordStrength.value <= 75) return t('auth.passwordGood')
  return t('auth.passwordStrong')
})

const validatePassword = () => {
  hasInteracted.value = true
}

// Confirm password validation
const confirmPasswordError = computed(() => {
  if (!form.confirmPassword) return ''
  if (form.confirmPassword !== form.password) return t('error.passwordMismatch')
  return ''
})

// Captcha validation
const captchaError = computed(() => {
  if (!form.captchaCode) return ''
  if (form.captchaCode.length !== 4) return t('error.captchaLength')
  return ''
})

// Form validation
const isFormValid = computed(() => {
  return (
    form.username &&
    !usernameError.value &&
    form.email &&
    !emailError.value &&
    passwordStrength.value === 100 &&
    form.confirmPassword &&
    !confirmPasswordError.value &&
    form.captchaCode &&
    form.captchaCode.length === 4
  )
})

const formSummaryError = computed(() => {
  if (!form.username) return t('error.usernameRequired')
  if (usernameError.value) return usernameError.value
  if (!form.email) return t('error.emailRequired')
  if (emailError.value) return emailError.value
  if (!form.password) return t('error.passwordRequired')
  if (passwordStrength.value < 100) return t('error.passwordStrengthInsufficient')
  if (!form.confirmPassword) return t('error.confirmPasswordRequired')
  if (confirmPasswordError.value) return confirmPasswordError.value
  if (!form.captchaCode) return t('error.captchaRequired')
  if (form.captchaCode.length !== 4) return t('error.captchaLength')
  return ''
})

const handleSubmit = async () => {
  hasInteracted.value = true
  
  if (!isFormValid.value) {
    ElMessage.error(formSummaryError.value || t('error.formInvalid'))
    return
  }
  
  loading.value = true
  try {
    // Send registration with captcha
    await api.post('/auth/register', {
      username: form.username,
      email: form.email,
      password: form.password,
      captcha_id: captchaId.value,
      captcha_code: form.captchaCode
    })
    ElMessage.success(t('auth.registerSuccess'))
    router.push('/login')
  } catch (error) {
    // Parse backend error message
    const detail = error.response?.data?.detail || ''
    let message = t('error.registerFailed')
    
    if (detail.includes('验证码') || detail.includes('captcha')) {
      message = t('error.invalidCaptcha')
      refreshCaptcha()  // Refresh captcha on error
    } else if (detail.includes('username') && detail.includes('taken')) {
      message = t('error.usernameExists')
    } else if (detail.includes('email') && detail.includes('taken')) {
      message = t('error.emailExists')
    } else if (detail.includes('Username already')) {
      message = t('error.usernameExists')
    } else if (detail.includes('Email already')) {
      message = t('error.emailExists')
    } else if (detail.includes('username') && detail.includes('invalid')) {
      message = t('error.invalidUsername')
    } else if (detail.includes('email') && detail.includes('invalid')) {
      message = t('error.invalidEmail')
    } else if (detail.includes('password') && detail.includes('weak')) {
      message = t('error.passwordStrengthInsufficient')
    } else if (detail.includes('频繁') || detail.includes('rate')) {
      message = t('error.tooManyRequests')
    } else if (detail) {
      message = detail
    }
    
    // Always refresh captcha after failed attempt
    refreshCaptcha()
    ElMessage.error(message)
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
  max-width: 420px;
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
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-error {
  font-size: 12px;
  color: var(--accent-danger);
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-summary-error {
  font-size: 12px;
  color: var(--accent-danger);
  text-align: center;
  margin-top: 8px;
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

.form-input-check {
  position: absolute;
  right: 14px;
  color: var(--accent-success);
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
  
  &.is-error {
    border-color: var(--accent-danger);
    background: var(--accent-danger-bg);
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

// Password Requirements
.password-requirements {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 12px;
  margin-top: 4px;
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 12px;
    color: var(--text-tertiary);
  }
  
  &__bar {
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 12px;
  }
  
  &__fill {
    height: 100%;
    border-radius: 2px;
    transition: all 0.2s;
    
    &.is-weak { background: #EF4444; }
    &.is-fair { background: #F59E0B; }
    &.is-good { background: #22C55E; }
    &.is-strong { background: #10B981; }
  }
  
  &__list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }
}

.password-strength-text {
  font-weight: 500;
  
  &.is-weak { color: #EF4444; }
  &.is-fair { color: #F59E0B; }
  &.is-good { color: #22C55E; }
  &.is-strong { color: #10B981; }
}

.requirement {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
  
  svg {
    flex-shrink: 0;
  }
  
  &.is-met {
    color: var(--accent-success);
  }
}

.auth-link {
  font-size: var(--text-sm);
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
  
  &:hover {
    text-decoration: underline;
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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
    
    &:hover:not(:disabled) {
      opacity: 0.9;
    }
  }
  
  &--full {
    width: 100%;
  }
  
  &--lg {
    padding: 16px 32px;
    font-size: var(--text-base);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

// Captcha
.captcha-row {
  display: flex;
  gap: 12px;
  align-items: stretch;
}

.captcha-input-wrapper {
  flex: 1;
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
</style>
