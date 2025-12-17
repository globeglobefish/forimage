<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Loading -->
      <div v-if="loading" class="status-box">
        <div class="status-icon status-icon--loading">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
        </div>
        <h3 class="status-title">{{ $t('auth.verifyingEmail') }}</h3>
        <p class="status-desc">{{ $t('common.pleaseWait') }}</p>
      </div>
      
      <!-- Success -->
      <div v-else-if="success" class="status-box">
        <div class="status-icon status-icon--success">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22,4 12,14.01 9,11.01"/>
          </svg>
        </div>
        <h3 class="status-title">{{ $t('auth.emailVerified') }}</h3>
        <p class="status-desc">{{ $t('auth.emailVerifiedHint') }}</p>
        <router-link to="/login">
          <button class="btn btn--primary btn--lg">{{ $t('auth.loginNow') }}</button>
        </router-link>
      </div>
      
      <!-- Error -->
      <div v-else class="status-box">
        <div class="status-icon status-icon--error">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h3 class="status-title">{{ $t('auth.verificationFailed') }}</h3>
        <p class="status-desc">{{ errorMessage }}</p>
        <router-link to="/login">
          <button class="btn btn--primary btn--lg">{{ $t('auth.backToLogin') }}</button>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const route = useRoute()
const loading = ref(true)
const success = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  const token = route.query.token
  
  if (!token) {
    loading.value = false
    errorMessage.value = t('error.invalidVerifyLink')
    return
  }
  
  try {
    await api.get('/auth/verify-email', { params: { token } })
    success.value = true
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || t('error.verificationFailed')
  } finally {
    loading.value = false
  }
})
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
  padding: 48px 40px;
  box-shadow: var(--shadow-neu-flat);
  text-align: center;
}

.status-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.status-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-bottom: 24px;
  
  &--loading {
    background: var(--bg-secondary);
    color: var(--text-tertiary);
    
    svg {
      animation: spin 1s linear infinite;
    }
  }
  
  &--success {
    background: var(--accent-success-bg);
    color: var(--accent-success);
  }
  
  &--error {
    background: var(--accent-danger-bg);
    color: var(--accent-danger);
  }
}

.status-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.status-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0 0 24px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 32px;
  font-size: 15px;
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover { opacity: 0.9; }
  }
  
  &--lg {
    padding: 16px 40px;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
