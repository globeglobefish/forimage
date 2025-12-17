<template>
  <div class="admin-page">
    <h2 class="admin-page__title">{{ $t('admin.images') }}</h2>
    
    <div class="filter-bar">
      <div class="search-box">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input v-model="search" type="text" :placeholder="$t('admin.searchFilename')" @keyup.enter="loadImages" />
      </div>
      <select v-model="statusFilter" class="filter-select" @change="loadImages">
        <option value="">{{ $t('admin.allStatus') }}</option>
        <option value="approved">{{ $t('admin.approved') }}</option>
        <option value="pending">{{ $t('admin.pending') }}</option>
        <option value="rejected">{{ $t('admin.rejected') }}</option>
      </select>
    </div>
    
    <div class="table-card">
      <div v-if="loading" class="loading">
        <div class="loading__spinner"></div>
      </div>
      
      <table v-else class="data-table">
        <thead>
          <tr>
            <th style="width: 80px">{{ $t('admin.preview') }}</th>
            <th>{{ $t('admin.filename') }}</th>
            <th>{{ $t('admin.user') }}</th>
            <th>{{ $t('admin.uploadIP') }}</th>
            <th>{{ $t('admin.dimensions') }}</th>
            <th>{{ $t('common.size') }}</th>
            <th>{{ $t('common.status') }}</th>
            <th>{{ $t('admin.uploadTime') }}</th>
            <th>{{ $t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="image in images" :key="image.id">
            <td>
              <img :src="image.url" class="preview-img" @click="showPreview(image)" />
            </td>
            <td class="cell-primary">
              <div class="image-name">{{ image.title || image.original_filename }}</div>
              <div v-if="image.title" class="image-filename">{{ image.original_filename }}</div>
            </td>
            <td>{{ image.username || $t('admin.guest') }}</td>
            <td class="cell-muted cell-ip">{{ image.upload_ip || image.guest_ip || '-' }}</td>
            <td class="cell-muted">{{ image.width }}×{{ image.height }}</td>
            <td class="cell-muted">{{ formatSize(image.file_size) }}</td>
            <td>
              <span class="badge" :class="getStatusClass(image.status)">
                {{ getStatusText(image.status) }}
              </span>
            </td>
            <td class="cell-muted">{{ formatDate(image.created_at) }}</td>
            <td>
              <div class="action-btns">
                <button 
                  v-if="image.status !== 'approved'" 
                  class="action-btn action-btn--success" 
                  @click="updateStatus(image, 'approved')" 
                  :title="$t('admin.approve')"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"/>
                  </svg>
                </button>
                <button 
                  v-if="image.status !== 'rejected'" 
                  class="action-btn action-btn--warning" 
                  @click="updateStatus(image, 'rejected')" 
                  :title="$t('admin.reject')"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
                <button class="action-btn action-btn--danger" @click="deleteImage(image)" :title="$t('common.delete')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3,6 5,6 21,6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="images.length === 0">
            <td colspan="9" class="empty-cell">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="total > pageSize" class="table-pagination">
        <span class="table-pagination__info">{{ $t('admin.totalItems', { count: total }) }}</span>
        <div class="table-pagination__btns">
          <button :disabled="page <= 1" @click="page--; loadImages()">{{ $t('common.prev') }}</button>
          <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
          <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; loadImages()">{{ $t('common.next') }}</button>
        </div>
      </div>
    </div>
    
    <!-- Preview Dialog -->
    <div v-if="previewVisible" class="dialog-overlay" @click.self="previewVisible = false">
      <div class="dialog dialog--lg">
        <div class="dialog__header">
          <h3>{{ previewImage?.original_filename }}</h3>
          <button class="dialog__close" @click="previewVisible = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog__body" v-if="previewImage">
          <img :src="previewImage.url" class="preview-large" />
          <div class="preview-info">
            <span>{{ previewImage.width }}×{{ previewImage.height }}</span>
            <span>{{ formatSize(previewImage.file_size) }}</span>
            <span>{{ formatDate(previewImage.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'

const { t } = useI18n()
const siteStore = useSiteStore()

const images = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const search = ref('')
const statusFilter = ref('')

const previewVisible = ref(false)
const previewImage = ref(null)

const loadImages = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (search.value) params.search = search.value
    if (statusFilter.value) params.status = statusFilter.value
    
    console.log('Loading images with params:', params)
    const response = await api.get('/admin/images', { params })
    console.log('Images response:', response.data)
    images.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Error loading images:', error)
    ElMessage.error(t('admin.loadImagesFailed') + ': ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const showPreview = (image) => {
  previewImage.value = image
  previewVisible.value = true
}

const updateStatus = async (image, status) => {
  try {
    await api.put(`/admin/images/${image.id}/status`, { status })
    ElMessage.success(t('admin.statusUpdateSuccess'))
    loadImages()
  } catch (error) {
    console.error(error)
  }
}

const deleteImage = async (image) => {
  try {
    await ElMessageBox.confirm(t('admin.deleteImageConfirm'), t('admin.deleteConfirm'), { type: 'warning' })
    await api.delete(`/admin/images/${image.id}`)
    ElMessage.success(t('common.success'))
    loadImages()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const getStatusClass = (status) => {
  const classes = { approved: 'badge--success', pending: 'badge--warning', rejected: 'badge--danger' }
  return classes[status] || ''
}

const getStatusText = (status) => {
  const texts = { 
    approved: t('admin.approved'), 
    pending: t('admin.pending'), 
    rejected: t('admin.rejected') 
  }
  return texts[status] || status
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const formatDate = (date) => {
  return formatDateTime(date, siteStore.timezone())
}

onMounted(() => {
  loadImages()
})
</script>

<style lang="scss" scoped>
.admin-page {
  &__title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 24px;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  
  svg { color: var(--text-tertiary); flex-shrink: 0; }
  
  input {
    width: 200px;
    padding: 10px 0;
    font-size: 14px;
    color: var(--text-primary);
    background: transparent;
    border: none;
    
    &::placeholder { color: var(--text-tertiary); }
    &:focus { outline: none; }
  }
}

.filter-select {
  padding: 10px 32px 10px 12px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-card) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpolyline points='6,9 12,15 18,9'/%3E%3C/svg%3E") no-repeat right 10px center;
  border: none;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  appearance: none;
  
  &:focus { outline: none; }
}

.table-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-neu-flat);
  overflow: hidden;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 60px;
  
  &__spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-light);
    border-top-color: var(--text-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
}

@keyframes spin { to { transform: rotate(360deg); } }

.data-table {
  width: 100%;
  border-collapse: collapse;
  
  th, td {
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
  }
  
  th {
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-weight: 600;
  }
  
  td {
    border-top: 1px solid var(--border-light);
    color: var(--text-secondary);
  }
  
  .cell-primary { color: var(--text-primary); font-weight: 500; }
  .cell-muted { color: var(--text-tertiary); }
  .cell-ip { font-family: var(--font-mono, monospace); font-size: 12px; }
  .empty-cell { text-align: center; padding: 40px; color: var(--text-tertiary); }
  
  .image-name {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .image-filename {
    font-size: 11px;
    color: var(--text-tertiary);
    font-weight: 400;
    margin-top: 2px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  tbody tr:hover { background: var(--bg-secondary); }
}

.preview-img {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: transform 0.15s;
  
  &:hover { transform: scale(1.1); }
}

.badge {
  display: inline-block;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  
  &--success { background: var(--accent-success-bg); color: var(--accent-success); }
  &--warning { background: var(--accent-warning-bg); color: var(--accent-warning); }
  &--danger { background: var(--accent-danger-bg); color: var(--accent-danger); }
}

.action-btns {
  display: flex;
  gap: 4px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover { background: var(--bg-tertiary); color: var(--text-primary); }
  &--success:hover { background: var(--accent-success-bg); color: var(--accent-success); }
  &--warning:hover { background: var(--accent-warning-bg); color: var(--accent-warning); }
  &--danger:hover { background: var(--accent-danger-bg); color: var(--accent-danger); }
}

.table-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-top: 1px solid var(--border-light);
  
  &__info { font-size: 13px; color: var(--text-tertiary); }
  
  &__btns {
    display: flex;
    align-items: center;
    gap: 12px;
    
    button {
      padding: 6px 12px;
      font-size: 13px;
      background: var(--bg-secondary);
      border: none;
      border-radius: var(--radius-sm);
      color: var(--text-primary);
      cursor: pointer;
      
      &:hover:not(:disabled) { background: var(--bg-tertiary); }
      &:disabled { opacity: 0.4; cursor: not-allowed; }
    }
    
    span { font-size: 13px; color: var(--text-secondary); }
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
}

.dialog {
  width: 100%;
  max-width: 420px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  
  &--lg { max-width: 600px; }
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-light);
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  
  &__close {
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 4px;
    flex-shrink: 0;
    &:hover { color: var(--text-primary); }
  }
  
  &__body { padding: 24px; }
}

.preview-large {
  max-width: 100%;
  max-height: 400px;
  display: block;
  margin: 0 auto 16px;
  border-radius: var(--radius-md);
}

.preview-info {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 13px;
  color: var(--text-tertiary);
}
</style>
