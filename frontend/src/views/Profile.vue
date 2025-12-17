<template>
  <div class="page">
    <div class="page__header">
      <h1 class="page__title">{{ $t('profile.title') }}</h1>
    </div>
    
    <div class="profile-grid">
      <!-- Account Info -->
      <div class="profile-card">
        <h3 class="profile-card__title">{{ $t('profile.basicInfo') }}</h3>
        
        <div class="stats-row" v-if="stats">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_images }}</div>
            <div class="stat-label">{{ $t('profile.totalImages') }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_albums }}</div>
            <div class="stat-label">{{ $t('profile.totalAlbums') }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ formatSize(stats.total_storage_used) }}</div>
            <div class="stat-label">{{ $t('profile.storageUsed') }}</div>
          </div>
        </div>
        
        <div class="info-list">
          <div class="info-item">
            <span class="info-item__label">{{ $t('auth.username') }}</span>
            <span class="info-item__value">{{ userStore.user?.username }}</span>
          </div>
          <div class="info-item">
            <span class="info-item__label">{{ $t('auth.email') }}</span>
            <span class="info-item__value">{{ userStore.user?.email }}</span>
          </div>
          <div class="info-item">
            <span class="info-item__label">{{ $t('common.status') }}</span>
            <span class="info-item__value">
              <span class="badge badge--success" v-if="userStore.user?.email_verified">{{ $t('profile.verified') }}</span>
              <span class="badge badge--warning" v-else>{{ $t('profile.pending') }}</span>
            </span>
          </div>
          <div class="info-item">
            <span class="info-item__label">{{ $t('profile.registeredAt') }}</span>
            <span class="info-item__value">{{ formatDate(userStore.user?.created_at) }}</span>
          </div>
        </div>
      </div>
      
      <!-- Change Password -->
      <div class="profile-card">
        <h3 class="profile-card__title">{{ $t('auth.changePassword') }}</h3>
        
        <form class="password-form" @submit.prevent="changePassword">
          <div class="form-group">
            <label class="form-label">{{ $t('auth.currentPassword') }}</label>
            <div class="form-input-wrapper">
              <input
                v-model="passwordForm.current_password"
                :type="showCurrentPassword ? 'text' : 'password'"
                class="form-input"
                :placeholder="$t('auth.currentPassword')"
                required
              />
              <button type="button" class="form-input-toggle" @click="showCurrentPassword = !showCurrentPassword">
                <svg v-if="!showCurrentPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ $t('auth.newPassword') }}</label>
            <div class="form-input-wrapper">
              <input
                v-model="passwordForm.new_password"
                :type="showNewPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'is-error': passwordForm.new_password && newPasswordError }"
                :placeholder="$t('auth.newPassword')"
                required
              />
              <button type="button" class="form-input-toggle" @click="showNewPassword = !showNewPassword">
                <svg v-if="!showNewPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
            <span class="form-hint">{{ $t('auth.passwordRequirements') }}</span>
            <span v-if="passwordForm.new_password && newPasswordError" class="form-error">{{ newPasswordError }}</span>
          </div>
          
          <div class="form-group">
            <label class="form-label">{{ $t('auth.confirmPassword') }}</label>
            <div class="form-input-wrapper">
              <input
                v-model="passwordForm.confirm_password"
                :type="showNewPassword ? 'text' : 'password'"
                class="form-input"
                :class="{ 'is-error': passwordForm.confirm_password && confirmPasswordError }"
                :placeholder="$t('auth.confirmPasswordPlaceholder')"
                required
              />
            </div>
            <span v-if="passwordForm.confirm_password && confirmPasswordError" class="form-error">{{ confirmPasswordError }}</span>
          </div>
          
          <button type="submit" class="btn btn--primary" :disabled="changingPassword || !isPasswordFormValid">
            <span v-if="changingPassword" class="btn-loader"></span>
            {{ changingPassword ? $t('common.loading') : $t('auth.changePassword') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'

const { t } = useI18n()
const siteStore = useSiteStore()
const userStore = useUserStore()

const stats = ref(null)
const changingPassword = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const newPasswordError = computed(() => {
  const p = passwordForm.new_password
  if (!p) return ''
  if (p.length < 8) return t('error.passwordTooShort')
  if (!/[a-z]/.test(p)) return t('error.passwordNeedsLower')
  if (!/[A-Z]/.test(p)) return t('error.passwordNeedsUpper')
  if (!/\d/.test(p)) return t('error.passwordNeedsDigit')
  return ''
})

const confirmPasswordError = computed(() => {
  if (!passwordForm.confirm_password) return ''
  if (passwordForm.confirm_password !== passwordForm.new_password) return t('error.passwordMismatch')
  return ''
})

const isPasswordFormValid = computed(() => {
  return (
    passwordForm.current_password &&
    passwordForm.new_password &&
    !newPasswordError.value &&
    passwordForm.confirm_password &&
    !confirmPasswordError.value
  )
})

const loadStats = async () => {
  try {
    const response = await api.get('/user/me/stats')
    stats.value = response.data
  } catch (error) {
    console.error(error)
  }
}

const changePassword = async () => {
  if (!isPasswordFormValid.value) return
  
  changingPassword.value = true
  try {
    await api.post('/user/me/change-password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success(t('profile.passwordUpdateSuccess'))
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (error) {
    const msg = error.response?.data?.detail || t('error.saveFailed')
    ElMessage.error(msg === 'Current password is incorrect' ? t('error.currentPasswordWrong') : msg)
  } finally {
    changingPassword.value = false
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const formatDate = (date) => {
  if (!date) return '-'
  return formatDateTime(date, siteStore.timezone())
}

onMounted(() => {
  loadStats()
})
</script>

<style lang="scss" scoped>
.page {
  max-width: 900px;
  margin: 0 auto;
  
  &__header {
    margin-bottom: 24px;
  }
  
  &__title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.profile-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-neu-flat);
  
  &__title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-light);
  }
}

.stats-row {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.stat-item {
  text-align: center;
  flex: 1;
  
  .stat-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .stat-label {
    font-size: 12px;
    color: var(--text-tertiary);
    margin-top: 4px;
  }
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  
  &__label {
    font-size: 13px;
    color: var(--text-tertiary);
  }
  
  &__value {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 500;
  border-radius: var(--radius-full);
  
  &--success {
    background: var(--accent-success-bg);
    color: var(--accent-success);
  }
  
  &--warning {
    background: var(--accent-warning-bg);
    color: var(--accent-warning);
  }
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
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

.form-input {
  width: 100%;
  padding: 12px 40px 12px 14px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  transition: all 0.15s;
  
  &::placeholder { color: var(--text-tertiary); }
  
  &:focus {
    outline: none;
    background: var(--bg-card);
    border-color: var(--border-medium);
  }
  
  &.is-error {
    border-color: var(--accent-danger);
  }
}

.form-input-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  padding: 4px;
  
  &:hover { color: var(--text-secondary); }
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover:not(:disabled) { opacity: 0.9; }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
}

.btn-loader {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
