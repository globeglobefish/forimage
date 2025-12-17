<template>
  <div class="home">
    <!-- Ban Notice -->
    <div v-if="banStatus.is_banned" class="ban-notice">
      <div class="ban-notice__icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
      </div>
      <div class="ban-notice__content">
        <h3>{{ $t('appeal.banNotice') }}</h3>
        <p class="ban-notice__reason">{{ $t('appeal.banReason', { reason: banStatus.reason || $t('appeal.defaultReason') }) }}</p>
        <p v-if="banStatus.expires_at" class="ban-notice__expires">
          {{ $t('appeal.banExpires', { time: formatBanExpiry(banStatus.expires_at) }) }}
        </p>
        <p v-else class="ban-notice__expires ban-notice__expires--permanent">{{ $t('appeal.banPermanent') }}</p>
        
        <!-- Appeal Section -->
        <div v-if="userStore.isLoggedIn" class="ban-notice__appeal">
          <template v-if="banStatus.existing_appeal">
            <div class="appeal-status">
              <span class="appeal-status__label">{{ $t('appeal.appealStatus') }}：</span>
              <span :class="['appeal-status__value', 'appeal-status__value--' + banStatus.existing_appeal.status]">
                {{ getAppealStatusText(banStatus.existing_appeal.status) }}
              </span>
            </div>
            <p v-if="banStatus.existing_appeal.admin_response" class="appeal-response">
              {{ $t('appeal.adminResponse') }}：{{ banStatus.existing_appeal.admin_response }}
            </p>
          </template>
          <button 
            v-if="banStatus.can_appeal" 
            class="btn btn--appeal" 
            @click="showAppealDialog = true"
          >
            {{ $t('appeal.submitAppeal') }}
          </button>
        </div>
        <p v-else class="ban-notice__login-hint">
          <router-link to="/login">{{ $t('auth.login') }}</router-link> {{ $t('appeal.loginToAppeal') }}
        </p>
      </div>
    </div>
    
    <div class="home__card">
      <!-- Left Panel -->
      <div class="home__left">
        <div class="brand">
          <img v-if="currentLogo" :src="currentLogo" :alt="siteStore.siteName()" class="brand__logo" />
          <h1 v-else class="brand__name">{{ siteStore.siteName() }}</h1>
          <p class="brand__tagline">{{ siteStore.siteSlogan() }}</p>
        </div>
        
        <div class="features">
          <div class="feature"><span class="feature__dot"></span>{{ $t('home.globalCDN') }}</div>
          <div class="feature"><span class="feature__dot"></span>{{ $t('home.backupStorage') }}</div>
          <div class="feature"><span class="feature__dot"></span>{{ $t('home.freeStorage') }}</div>
        </div>
        
        <div class="divider"></div>
        
        <table class="compare">
          <thead>
            <tr>
              <th></th>
              <th>{{ $t('home.guest') }}</th>
              <th>{{ $t('home.member') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ $t('home.singleFile') }}</td>
              <td>{{ siteStore.maxSizeGuestMB() }} MB</td>
              <td class="is-em">{{ siteStore.maxSizeUserMB() }} MB</td>
            </tr>
            <tr>
              <td>{{ $t('home.frequency') }}</td>
              <td>{{ guestRateLimitText }}</td>
              <td class="is-em">{{ userRateLimitText }}</td>
            </tr>
            <tr>
              <td>{{ $t('home.createAlbum') }}</td>
              <td class="is-muted">—</td>
              <td class="is-em">✓</td>
            </tr>
            <tr>
              <td>{{ $t('home.imageNaming') }}</td>
              <td class="is-muted">—</td>
              <td class="is-em">✓</td>
            </tr>
            <tr>
              <td>{{ $t('home.imageManagement') }}</td>
              <td class="is-muted">—</td>
              <td class="is-em">✓</td>
            </tr>
          </tbody>
        </table>
        
        <router-link v-if="!userStore.isLoggedIn" to="/register" class="cta">
          {{ $t('home.freeRegister') }} <span class="cta__arrow">→</span>
        </router-link>
      </div>
      
      <!-- Right Panel -->
      <div class="home__right">
        <div
          class="upload"
          :class="{ 'is-dragover': isDragover, 'is-disabled': banStatus.is_banned }"
          @click="!banStatus.is_banned && triggerFileInput()"
          @dragover.prevent="!banStatus.is_banned && handleDragOver()"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="!banStatus.is_banned && handleDrop($event)"
          tabindex="0"
          @keydown.enter="!banStatus.is_banned && triggerFileInput()"
          @keydown.space.prevent="!banStatus.is_banned && triggerFileInput()"
        >
          <template v-if="banStatus.is_banned">
            <svg class="upload__icon upload__icon--banned" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <p class="upload__title">{{ $t('home.uploadDisabled') }}</p>
            <p class="upload__hint">{{ $t('home.viewBanDetails') }}</p>
          </template>
          <template v-else>
            <svg class="upload__icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17,8 12,3 7,8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <p class="upload__title">{{ $t('home.dragOrClick') }}</p>
            <p class="upload__hint">{{ $t('home.pasteHint') }}</p>
            <p class="upload__formats">{{ allowedExtensions.join(' / ').toUpperCase() }} · {{ maxSizeMB }}MB</p>
          </template>
        </div>
        
        <input
          ref="fileInput"
          type="file"
          :accept="acceptTypes"
          multiple
          hidden
          @change="handleFileSelect"
        />
      </div>
    </div>
    
    <!-- Upload Results (below the card) -->
    <div v-if="uploadingFiles.length > 0 || uploadedImages.length > 0" class="results-area">
      <!-- Progress -->
      <div v-if="uploadingFiles.length > 0" class="progress-list">
        <div v-for="file in uploadingFiles" :key="file.id" class="progress-item">
          <span class="progress-item__name">{{ file.name }}</span>
          <div class="progress-item__bar">
            <div 
              class="progress-item__fill"
              :class="{ 'is-error': file.status === 'exception' }"
              :style="{ width: file.progress + '%' }"
            />
          </div>
          <span class="progress-item__pct">{{ file.progress }}%</span>
        </div>
      </div>
      
      <!-- Results -->
      <div v-if="uploadedImages.length > 0" class="results">
        <div class="results__head">
          <span>{{ $t('home.uploadSuccess') }} {{ uploadedImages.length }}</span>
          <button @click="clearResults">{{ $t('home.clearResults') }}</button>
        </div>
        
        <div v-for="img in uploadedImages" :key="img.id" class="result-card">
          <img :src="img.url" :alt="img.original_filename" class="result-card__thumb" />
          <div class="result-card__info">
            <div class="result-card__name">{{ img.original_filename }}</div>
            <div class="result-card__meta">{{ img.width }}×{{ img.height }} · {{ formatSize(img.file_size) }}</div>
          </div>
          <div class="result-card__links">
            <div class="link-row">
              <span class="link-row__label">URL</span>
              <input :value="img.fullUrl" readonly @focus="$event.target.select()" />
              <button @click="copyToClipboard(img.fullUrl)" :title="$t('common.copy')">{{ $t('common.copy') }}</button>
            </div>
            <div class="link-row">
              <span class="link-row__label">MD</span>
              <input :value="img.markdown" readonly @focus="$event.target.select()" />
              <button @click="copyToClipboard(img.markdown)" :title="$t('common.copy')">{{ $t('common.copy') }}</button>
            </div>
            <div class="link-row">
              <span class="link-row__label">HTML</span>
              <input :value="img.html" readonly @focus="$event.target.select()" />
              <button @click="copyToClipboard(img.html)" :title="$t('common.copy')">{{ $t('common.copy') }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Appeal Dialog -->
    <div v-if="showAppealDialog" class="dialog-overlay" @click.self="showAppealDialog = false">
      <div class="dialog">
        <div class="dialog__header">
          <h3>{{ $t('appeal.submitAppeal') }}</h3>
          <button class="dialog__close" @click="showAppealDialog = false">&times;</button>
        </div>
        <div class="dialog__body">
          <p class="dialog__hint">{{ $t('appeal.appealHint') }}</p>
          <textarea 
            v-model="appealReason" 
            class="dialog__textarea"
            :placeholder="$t('appeal.appealReasonPlaceholder')"
            rows="4"
          ></textarea>
        </div>
        <div class="dialog__footer">
          <button class="btn btn--secondary" @click="showAppealDialog = false">{{ $t('common.cancel') }}</button>
          <button 
            class="btn btn--primary" 
            @click="submitAppeal" 
            :disabled="!appealReason.trim() || submittingAppeal"
          >
            {{ submittingAppeal ? $t('common.loading') : $t('appeal.submitAppeal') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'
import { useThemeStore } from '@/stores/theme'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { formatDateTime } from '@/utils/timezone'

const { t } = useI18n()
const userStore = useUserStore()
const siteStore = useSiteStore()
const themeStore = useThemeStore()

// Logo based on theme - use dark logo if available in dark mode
const currentLogo = computed(() => {
  if (themeStore.isDark && siteStore.siteLogoDark()) {
    return siteStore.siteLogoDark()
  }
  return siteStore.siteLogo()
})
const fileInput = ref(null)
const isDragover = ref(false)
const uploadingFiles = ref([])
const uploadedImages = ref([])

// Ban status
const banStatus = reactive({
  is_banned: false,
  ban_id: null,
  reason: null,
  ban_type: null,
  expires_at: null,
  can_appeal: false,
  existing_appeal: null,
})
const showAppealDialog = ref(false)
const appealReason = ref('')
const submittingAppeal = ref(false)

// Dynamic settings from database
const allowedExtensions = computed(() => siteStore.allowedExtensions())
const acceptTypes = computed(() => siteStore.allowedExtensions().map(ext => `image/${ext === 'jpg' ? 'jpeg' : ext}`).join(','))
const maxSizeMB = computed(() => userStore.isLoggedIn ? siteStore.maxSizeUserMB() : siteStore.maxSizeGuestMB())
const maxSizeBytes = computed(() => userStore.isLoggedIn ? siteStore.maxSizeUser() : siteStore.maxSizeGuest())

// Rate limits - only show per hour for cleaner display
const guestRateLimitText = computed(() => `${siteStore.guestRateLimitPerHour()}${t('home.perHour')}`)
const userRateLimitText = computed(() => `${siteStore.userRateLimitPerHour()}${t('home.perHour')}`)

const triggerFileInput = () => fileInput.value?.click()
const handleDragOver = () => { isDragover.value = true }
const handleDragLeave = () => { isDragover.value = false }

const handleFileSelect = (e) => {
  uploadFiles(Array.from(e.target.files))
  e.target.value = ''
}

const handleDrop = (e) => {
  isDragover.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
  if (files.length) uploadFiles(files)
}

const handlePaste = (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  const items = e.clipboardData?.items
  if (!items) return
  const files = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  if (files.length) uploadFiles(files)
}

const validateFile = (file) => {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!allowedExtensions.value.includes(ext) && !file.type.startsWith('image/')) {
    ElMessage.error(t('error.unsupportedFormat', { format: file.name }))
    return false
  }
  if (file.size > maxSizeBytes.value) {
    ElMessage.error(t('error.fileTooLarge', { size: maxSizeMB.value }))
    return false
  }
  return true
}

const uploadFiles = async (files) => {
  for (const file of files) {
    if (!validateFile(file)) continue
    const item = { id: Date.now() + Math.random(), name: file.name, progress: 0, status: null }
    uploadingFiles.value.push(item)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => { item.progress = Math.round((e.loaded / e.total) * 100) },
      })
      item.status = 'success'
      
      const imageUrl = res.data.url
      // 如果 URL 已经是完整的（以 http 开头），直接使用；否则拼接 origin
      const fullUrl = imageUrl.startsWith('http') ? imageUrl : window.location.origin + imageUrl
      
      uploadedImages.value.unshift({
        ...res.data.image,
        url: imageUrl,
        fullUrl,
        markdown: `![${res.data.image.original_filename}](${fullUrl})`,
        html: `<img src="${fullUrl}" alt="${res.data.image.original_filename}">`,
      })
      
      setTimeout(() => {
        const idx = uploadingFiles.value.indexOf(item)
        if (idx > -1) uploadingFiles.value.splice(idx, 1)
      }, 500)
    } catch {
      item.status = 'exception'
      setTimeout(() => {
        const idx = uploadingFiles.value.indexOf(item)
        if (idx > -1) uploadingFiles.value.splice(idx, 1)
      }, 2000)
    }
  }
}

const copyToClipboard = async (text) => {
  try {
    // 优先使用现代 Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      ElMessage.success(t('common.copied'))
      return
    }
    // Fallback: 使用传统方法（支持非 HTTPS 环境）
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    textArea.style.top = '-9999px'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    if (successful) {
      ElMessage.success(t('common.copied'))
    } else {
      ElMessage.error(t('error.copyFailed'))
    }
  } catch {
    ElMessage.error(t('error.copyFailed'))
  }
}

const clearResults = () => { uploadedImages.value = [] }

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

// Ban status functions
const checkBanStatus = async () => {
  if (!userStore.isLoggedIn) {
    // Reset ban status for guests (they'll get error on upload attempt)
    Object.assign(banStatus, {
      is_banned: false,
      ban_id: null,
      reason: null,
      ban_type: null,
      expires_at: null,
      can_appeal: false,
      existing_appeal: null,
    })
    return
  }
  
  try {
    const res = await api.get('/appeal/status')
    Object.assign(banStatus, res.data)
  } catch (e) {
    console.error('Failed to check ban status:', e)
  }
}

const formatBanExpiry = (dateStr) => {
  return formatDateTime(dateStr, siteStore.timezone())
}

const getAppealStatusText = (status) => {
  const statusMap = {
    pending: t('appeal.statusPending'),
    approved: t('appeal.statusApproved'),
    rejected: t('appeal.statusRejected')
  }
  return statusMap[status] || status
}

const submitAppeal = async () => {
  if (!appealReason.value.trim()) return
  
  submittingAppeal.value = true
  try {
    await api.post('/appeal', { reason: appealReason.value.trim() })
    ElMessage.success(t('appeal.submitSuccess'))
    showAppealDialog.value = false
    appealReason.value = ''
    // Refresh ban status to show appeal
    await checkBanStatus()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || t('error.saveFailed'))
  } finally {
    submittingAppeal.value = false
  }
}

// Watch for login status changes
watch(() => userStore.isLoggedIn, () => {
  checkBanStatus()
})

onMounted(() => {
  document.addEventListener('paste', handlePaste)
  checkBanStatus()
})
onUnmounted(() => document.removeEventListener('paste', handlePaste))
</script>

<style lang="scss" scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 140px);
  padding: 32px 48px;
}

// Ban Notice
.ban-notice {
  display: flex;
  gap: 16px;
  max-width: 1000px;
  width: 100%;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
  
  &__icon {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(239, 68, 68, 0.15);
    border-radius: 50%;
    color: #ef4444;
  }
  
  &__content {
    flex: 1;
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #ef4444;
      margin: 0 0 8px;
    }
  }
  
  &__reason {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0 0 4px;
  }
  
  &__expires {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 0 0 12px;
    
    &--permanent {
      color: #ef4444;
      font-weight: 500;
    }
  }
  
  &__appeal {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid rgba(239, 68, 68, 0.15);
  }
  
  &__login-hint {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 12px 0 0;
    
    a {
      color: var(--accent-primary);
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

.appeal-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  
  &__label {
    font-size: 13px;
    color: var(--text-tertiary);
  }
  
  &__value {
    font-size: 13px;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 4px;
    
    &--pending {
      background: rgba(234, 179, 8, 0.15);
      color: #ca8a04;
    }
    
    &--approved {
      background: rgba(34, 197, 94, 0.15);
      color: #16a34a;
    }
    
    &--rejected {
      background: rgba(239, 68, 68, 0.15);
      color: #ef4444;
    }
  }
}

.appeal-response {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--appeal {
    background: #ef4444;
    color: white;
    border-color: #ef4444;
    
    &:hover {
      background: #dc2626;
      border-color: #dc2626;
    }
  }
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-color: var(--accent-primary);
    
    &:hover {
      opacity: 0.9;
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  &--secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border-color: var(--border-medium);
    
    &:hover {
      background: var(--bg-tertiary);
      border-color: var(--border-dark);
    }
  }
}

// Dialog
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
  width: 100%;
  max-width: 480px;
  
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-light);
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
    }
  }
  
  &__close {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: 1px solid transparent;
    font-size: 20px;
    color: var(--text-tertiary);
    cursor: pointer;
    border-radius: 4px;
    
    &:hover {
      background: var(--bg-secondary);
      border-color: var(--border-light);
      color: var(--text-primary);
    }
  }
  
  &__body {
    padding: 20px;
  }
  
  &__hint {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 0 0 12px;
  }
  
  &__textarea {
    width: 100%;
    padding: 12px;
    font-size: 14px;
    color: var(--text-primary);
    background: var(--bg-secondary);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-md);
    resize: vertical;
    min-height: 100px;
    
    &::placeholder {
      color: var(--text-tertiary);
    }
    
    &:focus {
      outline: none;
      border-color: var(--border-dark);
    }
  }
  
  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--border-light);
  }
}

.home__card {
  display: flex;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
  overflow: hidden;
  max-width: 1000px;
  width: 100%;
  min-height: 420px;
}

.home__left {
  flex: 0 0 340px;
  padding: 40px 36px;
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
}

.home__right {
  flex: 1;
  padding: 40px 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

// Brand
.brand {
  margin-bottom: 28px;
  
  &__logo {
    // 固定高度，宽度自适应，避免切换时跳动
    height: 48px;
    width: auto;
    max-width: 180px;
    object-fit: contain;
    // 平滑过渡
    transition: opacity 0.2s ease;
  }
  
  &__name {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
  }
  
  &__tagline {
    font-size: 14px;
    color: var(--text-tertiary);
    margin-top: 6px;
  }
}

// Features
.features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 28px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--text-secondary);
  
  &__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-primary);
  }
}

.divider {
  height: 1px;
  background: var(--border-light);
  margin-bottom: 28px;
}

// Compare Table
.compare {
  width: 100%;
  font-size: 13px;
  border-collapse: collapse;
  margin-bottom: 28px;
  
  th, td {
    padding: 10px 0;
    text-align: center;
  }
  
  th {
    color: var(--text-tertiary);
    font-weight: 500;
  }
  
  th:first-child,
  td:first-child {
    text-align: left;
    color: var(--text-secondary);
  }
  
  td {
    color: var(--text-tertiary);
    border-top: 1px solid var(--border-light);
  }
  
  .is-em {
    color: var(--text-primary);
    font-weight: 600;
  }
  
  .is-muted {
    opacity: 0.5;
  }
}

// CTA
.cta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-inverse);
  background: var(--accent-primary);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  
  &__arrow {
    transition: transform 0.2s;
  }
  
  &:hover &__arrow {
    transform: translateX(3px);
  }
}

// Upload
.upload {
  width: 100%;
  height: 100%;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--border-medium);
  border-radius: var(--radius-lg);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  
  &:hover,
  &:focus,
  &.is-dragover {
    border-color: var(--text-tertiary);
    background: var(--bg-secondary);
    
    .upload__icon {
      transform: translateY(-4px);
      color: var(--text-secondary);
    }
  }
  
  &.is-disabled {
    cursor: not-allowed;
    opacity: 0.6;
    border-color: rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.05);
    
    &:hover,
    &:focus {
      border-color: rgba(239, 68, 68, 0.3);
      background: rgba(239, 68, 68, 0.05);
      
      .upload__icon {
        transform: none;
      }
    }
  }
  
  &__icon {
    color: var(--text-tertiary);
    margin-bottom: 16px;
    transition: all 0.2s;
    
    &--banned {
      color: #ef4444;
    }
  }
  
  &__title {
    font-size: 17px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 6px;
  }
  
  &__hint {
    font-size: 14px;
    color: var(--text-secondary);
  }
  
  &__formats {
    font-size: 12px;
    color: var(--text-tertiary);
    margin-top: 16px;
  }
}

// Results Area
.results-area {
  max-width: 1000px;
  width: 100%;
  margin-top: 32px;
}

.progress-list {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  
  &:last-child { margin-bottom: 0; }
  
  &__name {
    flex: 0 0 120px;
    font-size: 13px;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__bar {
    flex: 1;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }
  
  &__fill {
    height: 100%;
    background: var(--accent-primary);
    transition: width 0.15s;
    
    &.is-error { background: var(--accent-danger); }
  }
  
  &__pct {
    flex: 0 0 36px;
    font-size: 11px;
    color: var(--text-tertiary);
    text-align: right;
  }
}

.results {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  
  &__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    font-size: 13px;
    color: var(--text-secondary);
    
    button {
      background: none;
      border: none;
      color: var(--text-tertiary);
      cursor: pointer;
      font-size: 12px;
      
      &:hover { color: var(--text-secondary); }
    }
  }
}

.result-card {
  display: grid;
  grid-template-columns: 60px 1fr;
  grid-template-rows: auto auto;
  gap: 8px 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
  
  &:last-child { margin-bottom: 0; }
  
  &__thumb {
    grid-row: 1 / 3;
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: var(--radius-sm);
    background: var(--bg-tertiary);
  }
  
  &__info {
    align-self: center;
  }
  
  &__name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__meta {
    font-size: 11px;
    color: var(--text-tertiary);
    margin-top: 2px;
  }
  
  &__links {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

.link-row {
  display: flex;
  align-items: center;
  gap: 8px;
  
  &__label {
    flex: 0 0 32px;
    font-size: 10px;
    font-weight: 600;
    color: var(--text-tertiary);
    text-transform: uppercase;
  }
  
  input {
    flex: 1;
    min-width: 0;
    padding: 5px 8px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-primary);
    background: var(--bg-card);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-sm);
    outline: none;
    
    &:focus {
      border-color: var(--border-dark);
    }
  }
  
  button {
    flex: 0 0 auto;
    padding: 5px 10px;
    font-size: 11px;
    color: var(--text-primary);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.15s;
    
    &:hover {
      background: var(--bg-secondary);
      border-color: var(--border-dark);
    }
  }
}

// Responsive
@media (max-width: 860px) {
  .home {
    padding: 24px;
  }
  
  .home__card {
    flex-direction: column;
    min-height: auto;
  }
  
  .home__left {
    flex: none;
    padding: 32px;
  }
  
  .home__right {
    padding: 32px;
  }
  
  .upload {
    min-height: 200px;
  }
  
  .cta {
    align-self: center;
  }
}

@media (max-width: 480px) {
  .home__left,
  .home__right {
    padding: 24px;
  }
  
  .brand__name {
    font-size: 26px;
  }
}
</style>
