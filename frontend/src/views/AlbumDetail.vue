<template>
  <div class="page">
    <div class="page__header">
      <div class="page__header-left">
        <button class="back-btn" @click="$router.push('/albums')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          {{ $t('common.back') }}
        </button>
        <h1 class="page__title" v-if="album">{{ album.name }}</h1>
      </div>
      <div class="page__header-right" v-if="album">
        <ExportDropdown 
          :images="images"
          :album-id="albumId"
          :album-name="album.name"
          :disabled="total === 0"
        />
        <button class="btn btn--secondary btn--icon" @click="showEditDialog" :title="$t('albums.editAlbum')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
      </div>
    </div>
    
    <div v-if="album && album.description" class="album-desc">
      {{ album.description }}
    </div>
    
    <div class="filter-bar" v-if="!loading">
      <div class="filter-bar__left">
        <!-- Sort Options Dropdown -->
        <el-dropdown @command="handleSortChange" trigger="click">
          <button class="sort-dropdown-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M6 12h12M9 18h6"/>
            </svg>
            {{ $t('sort.sortBy') }}: {{ currentSortLabel }}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6,9 12,15 18,9"/>
            </svg>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="created_at_desc" :class="{ active: sortPreference === 'created_at_desc' }">
                {{ $t('sort.dateNewest') }}
              </el-dropdown-item>
              <el-dropdown-item command="created_at_asc" :class="{ active: sortPreference === 'created_at_asc' }">
                {{ $t('sort.dateOldest') }}
              </el-dropdown-item>
              <el-dropdown-item command="file_size_desc" :class="{ active: sortPreference === 'file_size_desc' }">
                {{ $t('sort.sizelargest') }}
              </el-dropdown-item>
              <el-dropdown-item command="file_size_asc" :class="{ active: sortPreference === 'file_size_asc' }">
                {{ $t('sort.sizeSmallest') }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- View Mode Toggle -->
        <div class="view-toggles">
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'masonry' }"
            @click="viewMode = 'masonry'"
            :title="$t('gallery.masonryView')"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/>
              <rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>
            </svg>
          </button>
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'grid' }"
            @click="viewMode = 'grid'"
            :title="$t('gallery.gridView')"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
          </button>
        </div>
      </div>
      <span class="filter-stats">{{ $t('albums.totalImages', { count: total }) }}</span>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>
    
    <div v-else-if="images.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21,15 16,10 5,21"/>
      </svg>
      <p>{{ $t('albums.noImagesInAlbum') }}</p>
      <p class="empty-state__hint">{{ $t('albums.moveImagesHint') }}</p>
      <button class="btn btn--primary" @click="$router.push('/my-images')">{{ $t('albums.manageImages') }}</button>
    </div>
    
    <template v-if="images.length > 0">
      <!-- Masonry View (Waterfall) -->
      <div v-if="viewMode === 'masonry'" class="masonry-grid">
        <div v-for="image in images" :key="image.id" class="masonry-item" @click="showDetail(image)">
          <img :src="image.url" :alt="image.title || image.original_filename" loading="lazy" />
          <div class="masonry-item__overlay">
            <span class="masonry-item__title">{{ image.title || image.original_filename }}</span>
            <div class="masonry-item__meta">{{ formatSize(image.file_size) }}</div>
          </div>
          <div class="masonry-item__actions" @click.stop>
            <button class="icon-btn" @click="copyUrl(image)" :title="$t('images.copyUrl')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </button>
            <button class="icon-btn" @click="removeFromAlbum(image)" :title="$t('images.removeFromAlbum')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
            <button class="icon-btn icon-btn--danger" @click="deleteImage(image)" :title="$t('common.delete')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Normal Grid View -->
      <div v-else class="image-grid">
        <div v-for="image in images" :key="image.id" class="image-card" @click="showDetail(image)">
          <div class="image-card__thumb">
            <img :src="image.url" :alt="image.title || image.original_filename" />
          </div>
          <div class="image-card__info">
            <div class="image-card__name">{{ image.title || image.original_filename }}</div>
            <div class="image-card__meta">{{ formatSize(image.file_size) }}</div>
          </div>
          <div class="image-card__actions" @click.stop>
            <button class="icon-btn" @click="copyUrl(image)" :title="$t('images.copyUrl')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </button>
            <button class="icon-btn" @click="removeFromAlbum(image)" :title="$t('images.removeFromAlbum')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
            <button class="icon-btn icon-btn--danger" @click="deleteImage(image)" :title="$t('common.delete')">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Loading More Indicator (for infinite scroll) -->
      <div v-if="loadingMore" class="loading-more">
        <div class="loading__spinner loading__spinner--small"></div>
        <span>{{ $t('common.loading') || '加载中...' }}</span>
      </div>
      
      <!-- Load More Trigger (intersection observer target) -->
      <div ref="loadMoreTrigger" class="load-more-trigger"></div>
      
      <!-- End of List -->
      <div v-if="!hasMore && images.length > 0" class="end-of-list">
        <span>{{ $t('common.noMore') || '没有更多了' }}</span>
      </div>
    </template>
    
    <!-- Detail Dialog -->
    <div v-if="detailVisible" class="dialog-overlay" @click.self="detailVisible = false">
      <div class="dialog dialog--lg">
        <div class="dialog__header">
          <h3>{{ selectedImage?.original_filename }}</h3>
          <button class="dialog__close" @click="detailVisible = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog__body" v-if="selectedImage">
          <img :src="selectedImage.url" class="detail-image" />
          <div class="detail-meta">
            <span>{{ selectedImage.width }} × {{ selectedImage.height }}</span>
            <span>{{ formatSize(selectedImage.file_size) }}</span>
            <span>{{ formatDate(selectedImage.created_at) }}</span>
          </div>
          <div class="detail-links">
            <div class="link-row">
              <span class="link-row__label">URL</span>
              <input :value="getFullUrl(selectedImage)" readonly class="link-row__input" @focus="$event.target.select()" />
              <button class="btn btn--small" @click="copyToClipboard(getFullUrl(selectedImage))">复制</button>
            </div>
            <div class="link-row">
              <span class="link-row__label">MD</span>
              <input :value="getMarkdown(selectedImage)" readonly class="link-row__input" @focus="$event.target.select()" />
              <button class="btn btn--small" @click="copyToClipboard(getMarkdown(selectedImage))">复制</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Edit Album Dialog -->
    <div v-if="editDialogVisible" class="dialog-overlay" @click.self="editDialogVisible = false">
      <div class="dialog">
        <div class="dialog__header">
          <h3>编辑相册</h3>
          <button class="dialog__close" @click="editDialogVisible = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog__body">
          <div class="form-group">
            <label class="form-label">相册名称 <span class="required">*</span></label>
            <input v-model="editForm.name" type="text" class="form-input" placeholder="输入相册名称" />
          </div>
          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea v-model="editForm.description" class="form-input form-textarea" placeholder="可选的描述" rows="3"></textarea>
          </div>
          <div class="form-group form-group--inline">
            <label class="form-label">公开相册</label>
            <label class="switch">
              <input type="checkbox" v-model="editForm.is_public" />
              <span class="switch__slider"></span>
            </label>
          </div>
        </div>
        <div class="dialog__footer">
          <button class="btn btn--secondary" @click="editDialogVisible = false">取消</button>
          <button class="btn btn--primary" @click="saveAlbum" :disabled="!editForm.name || saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'
import ExportDropdown from '@/components/ExportDropdown.vue'

const { t } = useI18n()
const siteStore = useSiteStore()

const route = useRoute()
const router = useRouter()

const album = ref(null)
const images = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 30  // Larger page size for infinite scroll
const total = ref(0)
const loadMoreTrigger = ref(null)

let intersectionObserver = null

const detailVisible = ref(false)
const selectedImage = ref(null)

const editDialogVisible = ref(false)
const saving = ref(false)
const editForm = reactive({
  name: '',
  description: '',
  is_public: false,
})

// Sorting state
const sortPreference = ref('created_at_desc')
const viewMode = ref('grid') // 'grid' or 'masonry' - default to grid

const albumId = route.params.id
const hasMore = computed(() => images.value.length < total.value)

// Computed sort label
const currentSortLabel = computed(() => {
  const labels = {
    'created_at_desc': t('sort.dateNewest'),
    'created_at_asc': t('sort.dateOldest'),
    'file_size_desc': t('sort.sizelargest'),
    'file_size_asc': t('sort.sizeSmallest'),
  }
  return labels[sortPreference.value] || t('sort.dateNewest')
})

const loadAlbum = async () => {
  try {
    const response = await api.get(`/albums/${albumId}`)
    album.value = response.data
  } catch (error) {
    ElMessage.error(t('albums.albumNotFound'))
    router.push('/albums')
  }
}

const loadImages = async (reset = false) => {
  if (reset) {
    page.value = 1
    images.value = []
  }
  
  if (loading.value || loadingMore.value) return
  if (!reset && !hasMore.value) return
  
  if (reset) {
    loading.value = true
  } else {
    loadingMore.value = true
  }
  
  try {
    // Parse sort preference
    const [sortBy, sortOrder] = sortPreference.value.split('_').reduce((acc, part, idx, arr) => {
      if (idx === arr.length - 1) {
        return [arr.slice(0, -1).join('_'), part]
      }
      return acc
    }, ['created_at', 'desc'])
    
    const response = await api.get('/images', {
      params: { 
        page: page.value, 
        page_size: pageSize, 
        album_id: albumId,
        sort_by: sortBy,
        sort_order: sortOrder
      }
    })
    
    if (reset) {
      images.value = response.data.items || []
    } else {
      images.value = [...images.value, ...(response.data.items || [])]
    }
    total.value = response.data.total || 0
    page.value++
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// Setup intersection observer for infinite scroll
const setupIntersectionObserver = () => {
  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }
  
  intersectionObserver = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry.isIntersecting && hasMore.value && !loading.value && !loadingMore.value) {
        loadImages(false)
      }
    },
    {
      root: null,
      rootMargin: '200px',
      threshold: 0
    }
  )
  
  nextTick(() => {
    if (loadMoreTrigger.value) {
      intersectionObserver.observe(loadMoreTrigger.value)
    }
  })
}

// Sort handling (local only, not persisted to backend)
const handleSortChange = (command) => {
  sortPreference.value = command
  // Reload images with new sort (reset to first page)
  loadImages(true)
}

const showDetail = (image) => {
  selectedImage.value = { ...image }
  detailVisible.value = true
}

const showEditDialog = () => {
  if (!album.value) return
  editForm.name = album.value.name
  editForm.description = album.value.description || ''
  editForm.is_public = album.value.is_public
  editDialogVisible.value = true
}

const saveAlbum = async () => {
  if (!editForm.name) return
  saving.value = true
  try {
    await api.put(`/albums/${albumId}`, editForm)
    album.value.name = editForm.name
    album.value.description = editForm.description
    album.value.is_public = editForm.is_public
    editDialogVisible.value = false
    ElMessage.success(t('common.success'))
  } catch (error) {
    console.error(error)
    ElMessage.error(t('error.saveFailed'))
  } finally {
    saving.value = false
  }
}

// 如果 URL 已经是完整的（云存储），直接使用；否则拼接 origin
const getFullUrl = (image) => image.url.startsWith('http') ? image.url : window.location.origin + image.url
const getMarkdown = (image) => `![${image.original_filename}](${getFullUrl(image)})`

const copyUrl = async (image) => {
  await copyToClipboard(getFullUrl(image))
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

const removeFromAlbum = async (image) => {
  try {
    await ElMessageBox.confirm('确定要将这张图片移出相册吗？图片不会被删除。', '移出相册', {
      confirmButtonText: '移出',
      cancelButtonText: '取消',
    })
    await api.put(`/images/${image.id}/move`, { album_id: null })
    ElMessage.success('已移出相册')
    loadImages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('操作失败')
    }
  }
}

const deleteImage = async (image) => {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？删除后无法恢复。', '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await api.delete(`/images/${image.id}`)
    ElMessage.success('删除成功')
    loadImages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('删除失败')
    }
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const formatDate = (date) => {
  if (!date) return '-'
  return formatDateTime(date, siteStore.timezone())
}

onMounted(async () => {
  await loadAlbum()
  await loadImages(true)
  setupIntersectionObserver()
})

onUnmounted(() => {
  if (intersectionObserver) {
    intersectionObserver.disconnect()
  }
})

// Re-setup observer when view mode changes
watch(viewMode, () => {
  nextTick(() => {
    setupIntersectionObserver()
  })
})
</script>

<style lang="scss" scoped>
.page {
  max-width: 1000px;
  margin: 0 auto;
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    &-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    &-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  &__title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
}

.album-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  
  &__left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.sort-dropdown-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
}

.filter-stats {
  font-size: 13px;
  color: var(--text-tertiary);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  gap: 16px;
  
  &__spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-light);
    border-top-color: var(--text-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  &__text {
    font-size: 14px;
    color: var(--text-tertiary);
    margin: 0;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
}

// Infinite scroll indicators
.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 30px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.loading__spinner--small {
  width: 24px;
  height: 24px;
  border-width: 2px;
  border: 2px solid var(--border-light);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.load-more-trigger {
  height: 1px;
  width: 100%;
}

.end-of-list {
  text-align: center;
  padding: 30px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  
  svg { margin-bottom: 16px; }
  p { margin: 0 0 8px; font-size: 15px; }
  
  &__hint {
    font-size: 13px;
    margin-bottom: 20px !important;
  }
}

// View toggles
.view-toggles {
  display: flex;
  gap: 4px;
  margin-left: 8px;
  padding-left: 12px;
  border-left: 1px solid var(--border-light);
}

.view-toggle {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  &.is-active {
    background: var(--accent-primary-bg, rgba(59, 130, 246, 0.1));
    color: var(--accent-primary);
  }
}

// Masonry (Waterfall) Layout
.masonry-grid {
  -webkit-column-count: 4;
  -moz-column-count: 4;
  column-count: 4;
  -webkit-column-gap: 16px;
  -moz-column-gap: 16px;
  column-gap: 16px;
  
  @media (max-width: 1200px) {
    -webkit-column-count: 3;
    -moz-column-count: 3;
    column-count: 3;
  }
  
  @media (max-width: 768px) {
    -webkit-column-count: 2;
    -moz-column-count: 2;
    column-count: 2;
  }
  
  @media (max-width: 480px) {
    -webkit-column-count: 1;
    -moz-column-count: 1;
    column-count: 1;
  }
}

.masonry-item {
  display: inline-block;
  width: 100%;
  -webkit-column-break-inside: avoid;
  page-break-inside: avoid;
  break-inside: avoid;
  margin-bottom: 16px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  position: relative;
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    
    .masonry-item__overlay {
      opacity: 1;
    }
    
    .masonry-item__actions {
      opacity: 1;
    }
  }
  
  img {
    width: 100%;
    height: auto;
    display: block;
  }
  
  &__overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 40px 12px 12px;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
    opacity: 0;
    transition: opacity 0.2s;
  }
  
  &__title {
    font-size: 13px;
    font-weight: 500;
    color: white;
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 4px;
  }
  
  &__meta {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  &__actions {
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
    
    .icon-btn {
      background: rgba(0, 0, 0, 0.5);
      color: white;
      
      &:hover {
        background: rgba(0, 0, 0, 0.7);
      }
      
      &--danger:hover {
        background: var(--accent-danger);
        color: white;
      }
    }
  }
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.image-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-neu-flat);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-neu-convex);
  }
  
  &__thumb {
    width: 100%;
    height: 140px;
    overflow: hidden;
    background: var(--bg-secondary);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  &__info {
    padding: 12px;
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
    margin-top: 4px;
  }
  
  &__actions {
    display: flex;
    justify-content: flex-end;
    gap: 4px;
    padding: 0 8px 8px;
  }
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  &--danger:hover {
    background: var(--accent-danger-bg);
    color: var(--accent-danger);
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  
  &__btn {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-card);
    border: none;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    box-shadow: var(--shadow-sm);
    
    &:hover:not(:disabled) { color: var(--text-primary); }
    &:disabled { opacity: 0.4; cursor: not-allowed; }
  }
  
  &__info {
    font-size: 14px;
    color: var(--text-secondary);
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    &:hover { opacity: 0.9; }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
  
  &--secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    &:hover { background: var(--bg-tertiary); }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
  
  &--icon {
    padding: 10px;
    gap: 0;
  }
  
  &--small {
    padding: 6px 12px;
    font-size: 12px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    &:hover { background: var(--bg-tertiary); }
  }
  
  &--outline {
    background: transparent;
    border: 1px solid var(--border-medium);
    color: var(--text-secondary);
    &:hover {
      background: var(--bg-secondary);
      color: var(--text-primary);
    }
  }
  
  &--active {
    background: var(--accent-primary-bg, rgba(59, 130, 246, 0.1));
    border-color: var(--accent-primary, #3b82f6);
    color: var(--accent-primary, #3b82f6);
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
  width: 100%;
  max-width: 420px;
  max-height: 90vh;
  overflow-y: auto;
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
      flex: 1;
      margin-right: 12px;
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
  
  &__body {
    padding: 24px;
  }
  
  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid var(--border-light);
  }
}

.detail-image {
  max-width: 100%;
  max-height: 300px;
  display: block;
  margin: 0 auto 20px;
  border-radius: var(--radius-md);
}

.detail-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.detail-links {
  margin-bottom: 0;
}

.link-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  
  &:last-child { margin-bottom: 0; }
  
  &__label {
    width: 32px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-tertiary);
    text-transform: uppercase;
    flex-shrink: 0;
  }
  
  &__input {
    flex: 1;
    padding: 8px 12px;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-primary);
    background: var(--bg-secondary);
    border: none;
    border-radius: var(--radius-sm);
    
    &:focus { outline: none; }
  }
}

// Form
.form-group {
  margin-bottom: 20px;
  
  &:last-child { margin-bottom: 0; }
  
  &--inline {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
  
  .required { color: var(--accent-danger); }
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  transition: all 0.15s;
  
  &::placeholder { color: var(--text-tertiary); }
  &:focus {
    outline: none;
    border-color: var(--border-medium);
    background: var(--bg-card);
  }
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  
  input {
    opacity: 0;
    width: 0;
    height: 0;
    
    &:checked + .switch__slider {
      background: var(--accent-primary);
      &::before { transform: translateX(20px); }
    }
  }
  
  &__slider {
    position: absolute;
    inset: 0;
    background: var(--bg-tertiary);
    border-radius: 12px;
    cursor: pointer;
    transition: 0.2s;
    
    &::before {
      content: '';
      position: absolute;
      left: 2px;
      top: 2px;
      width: 20px;
      height: 20px;
      background: white;
      border-radius: 50%;
      transition: 0.2s;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
  }
}
</style>
