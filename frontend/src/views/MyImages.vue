<template>
  <div class="page" ref="pageContainer">
    <div class="page__header">
      <h1 class="page__title">{{ $t('images.title') }}</h1>
      <div class="page__header-actions">
        <button 
          v-if="!batchMode" 
          class="header-btn" 
          @click="enterBatchMode"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
          </svg>
          {{ $t('images.batchManage') }}
        </button>
        <button class="header-btn header-btn--primary" @click="$router.push('/')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          {{ $t('common.upload') }}
        </button>
      </div>
    </div>
    
    <!-- Batch Mode Toolbar -->
    <div v-if="batchMode" class="batch-toolbar">
      <div class="batch-toolbar__left">
        <label class="checkbox-wrapper">
          <input 
            type="checkbox" 
            :checked="isAllSelected" 
            :indeterminate="isPartialSelected"
            @change="toggleSelectAll"
          />
          <span class="checkbox-label">{{ $t('images.selectAll') }}</span>
        </label>
        <span class="batch-toolbar__count">
          {{ $t('images.selectedCount', { count: selectedIds.length }) }}
        </span>
      </div>
      <div class="batch-toolbar__right">
        <select 
          v-model="batchMoveAlbumId" 
          class="filter-select"
          :disabled="selectedIds.length === 0"
        >
          <option :value="undefined" disabled>{{ $t('images.moveTo') }}</option>
          <option :value="null">{{ $t('images.uncategorized') }}</option>
          <option v-for="album in albums" :key="album.id" :value="album.id">{{ album.name }}</option>
        </select>
        <button 
          class="batch-btn" 
          :disabled="selectedIds.length === 0 || batchMoveAlbumId === undefined"
          @click="batchMove"
        >
          {{ $t('images.batchMove') }}
        </button>
        <ExportDropdown 
          :images="images"
          :selected-ids="selectedIds"
          album-name="images"
          :disabled="selectedIds.length === 0"
          btn-class="batch-btn"
        />
        <button 
          class="batch-btn batch-btn--danger" 
          :disabled="selectedIds.length === 0"
          @click="batchDelete"
        >
          {{ $t('images.batchDelete') }}
        </button>
        <button class="batch-btn batch-btn--cancel" @click="exitBatchMode">
          {{ $t('common.cancel') }}
        </button>
      </div>
    </div>
    
    <div class="filter-bar" :class="{ 'filter-bar--no-margin': showAdvancedSearch || hasActiveFilters }">
      <div class="filter-bar__left">
        <select v-model="albumFilter" class="filter-select" @change="handleFilterChange">
          <option :value="null">{{ $t('common.all') }}</option>
          <option :value="0">{{ $t('images.uncategorized') }}</option>
          <option v-for="album in albums" :key="album.id" :value="album.id">{{ album.name }}</option>
        </select>
        
        <!-- Advanced Search Toggle -->
        <button 
          class="filter-toggle-btn" 
          :class="{ 'is-active': showAdvancedSearch || hasActiveFilters }"
          @click="showAdvancedSearch = !showAdvancedSearch"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          {{ $t('search.title') }}
          <span v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</span>
        </button>
        
        <!-- View Mode Toggle -->
        <div class="view-toggles">
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'masonry' }"
            @click="switchViewMode('masonry')"
            :title="$t('gallery.masonryView') || '瀑布流'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/>
              <rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>
            </svg>
          </button>
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'grid' }"
            @click="switchViewMode('grid')"
            :title="$t('gallery.gridView') || '网格'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
          </button>
        </div>
      </div>
      <span v-if="total > 0" class="filter-stats">
        {{ $t('common.total') }} {{ total }}
        <template v-if="albumFilter === 0">（{{ $t('images.uncategorized') }}）</template>
        <template v-else-if="albumFilter !== null">（{{ currentAlbumName }}）</template>
      </span>
    </div>
    
    <!-- Advanced Search Panel (Expandable) -->
    <transition name="slide">
      <div v-if="showAdvancedSearch" class="search-panel">
        <div class="search-panel__row">
          <!-- Date Range -->
          <div class="search-field">
            <label class="search-field__label">{{ $t('search.dateRange') }}</label>
            <div class="search-field__inputs">
              <el-date-picker
                v-model="searchFilters.dateFrom"
                type="date"
                :placeholder="$t('search.dateFrom')"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                size="small"
                style="width: 130px"
              />
              <span class="search-field__sep">-</span>
              <el-date-picker
                v-model="searchFilters.dateTo"
                type="date"
                :placeholder="$t('search.dateTo')"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                size="small"
                style="width: 130px"
              />
            </div>
          </div>
          
          <!-- Dimensions -->
          <div class="search-field">
            <label class="search-field__label">{{ $t('search.dimensions') }}</label>
            <div class="search-field__inputs">
              <el-input-number v-model="searchFilters.minWidth" :min="0" :step="100" size="small" :placeholder="$t('search.minWidth')" controls-position="right" style="width: 100px" />
              <span class="search-field__sep">×</span>
              <el-input-number v-model="searchFilters.minHeight" :min="0" :step="100" size="small" :placeholder="$t('search.minHeight')" controls-position="right" style="width: 100px" />
              <span class="search-field__sep">~</span>
              <el-input-number v-model="searchFilters.maxWidth" :min="0" :step="100" size="small" :placeholder="$t('search.maxWidth')" controls-position="right" style="width: 100px" />
              <span class="search-field__sep">×</span>
              <el-input-number v-model="searchFilters.maxHeight" :min="0" :step="100" size="small" :placeholder="$t('search.maxHeight')" controls-position="right" style="width: 100px" />
            </div>
          </div>
        </div>
        
        <div class="search-panel__actions">
          <div class="preset-btns">
            <button class="preset-btn" @click="applyPreset('hd')">{{ $t('search.presetHD') }}</button>
            <button class="preset-btn" @click="applyPreset('fullhd')">{{ $t('search.presetFullHD') }}</button>
            <button class="preset-btn" @click="applyPreset('4k')">{{ $t('search.preset4K') }}</button>
          </div>
          <div class="action-btns">
            <button class="action-btn" @click="resetFilters">{{ $t('search.resetFilters') }}</button>
            <button class="action-btn action-btn--primary" @click="applyFilters">{{ $t('search.applyFilters') }}</button>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- Active Filters Display -->
    <div v-if="hasActiveFilters && !showAdvancedSearch" class="active-filters">
      <span class="active-filters__label">{{ $t('search.activeFilters') }}:</span>
      <span v-if="searchFilters.dateFrom || searchFilters.dateTo" class="filter-tag">
        {{ formatDateRange }}
        <button class="filter-tag__close" @click="clearDateFilter">×</button>
      </span>
      <span v-if="hasDimensionFilter" class="filter-tag">
        {{ formatDimensions }}
        <button class="filter-tag__close" @click="clearDimensionFilter">×</button>
      </span>
      <button class="clear-all-btn" @click="resetFilters">{{ $t('search.clearFilters') }}</button>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>
    
    <div v-else-if="images.length === 0" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21,15 16,10 5,21"/>
      </svg>
      <template v-if="hasActiveFilters">
        <p>{{ $t('search.noResults') }}</p>
        <p class="empty-state__hint">{{ $t('search.tryDifferent') }}</p>
      </template>
      <template v-else>
        <p v-if="albumFilter === 0">{{ $t('images.noUncategorized') }}</p>
        <p v-else-if="albumFilter !== null">{{ $t('images.noImagesInAlbum') }}</p>
        <p v-else>{{ $t('images.noImages') }}</p>
        <button class="btn btn--primary" @click="$router.push('/')">{{ $t('images.uploadFirst') }}</button>
      </template>
    </div>
    
    <template v-else>
      <!-- Masonry View (Waterfall) -->
      <div v-if="viewMode === 'masonry'" class="masonry-grid">
        <div 
          v-for="image in images" 
          :key="image.id" 
          class="masonry-item"
          :class="{ 'masonry-item--selected': selectedIds.includes(image.id) }"
          @click="handleCardClick(image)"
        >
          <!-- Batch mode checkbox -->
          <div v-if="batchMode" class="masonry-item__checkbox" @click.stop>
            <input 
              type="checkbox" 
              :checked="selectedIds.includes(image.id)"
              @change="toggleSelect(image.id)"
            />
          </div>
          <img :src="image.url" :alt="image.title || image.original_filename" loading="lazy" />
          <div class="masonry-item__overlay">
            <span class="masonry-item__title">{{ image.title || image.original_filename }}</span>
            <div class="masonry-item__meta">
              {{ formatSize(image.file_size) }} · {{ formatDate(image.created_at) }}
            </div>
            <div class="masonry-item__album" v-if="image.album_id && albumFilter === null">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              {{ getAlbumName(image.album_id) }}
            </div>
          </div>
          <div v-if="!batchMode" class="masonry-item__actions" @click.stop>
            <button class="icon-btn" @click="copyUrl(image)" title="复制链接">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </button>
            <button class="icon-btn icon-btn--danger" @click="deleteImage(image)" title="删除">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Grid View -->
      <div v-else class="image-grid">
        <div 
          v-for="image in images" 
          :key="image.id" 
          class="image-card"
          :class="{ 'image-card--selected': selectedIds.includes(image.id) }"
          @click="handleCardClick(image)"
        >
          <!-- Batch mode checkbox -->
          <div v-if="batchMode" class="image-card__checkbox" @click.stop>
            <input 
              type="checkbox" 
              :checked="selectedIds.includes(image.id)"
              @change="toggleSelect(image.id)"
            />
          </div>
          <div class="image-card__thumb">
            <img :src="image.url" :alt="image.title || image.original_filename" />
          </div>
          <div class="image-card__info">
            <div class="image-card__name">{{ image.title || image.original_filename }}</div>
            <div class="image-card__meta">
              {{ formatSize(image.file_size) }} · {{ formatDate(image.created_at) }}
            </div>
            <div class="image-card__album" v-if="image.album_id && albumFilter === null">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              {{ getAlbumName(image.album_id) }}
            </div>
          </div>
          <div v-if="!batchMode" class="image-card__actions" @click.stop>
            <button class="icon-btn" @click="copyUrl(image)" title="复制链接">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </button>
            <button class="icon-btn icon-btn--danger" @click="deleteImage(image)" title="删除">
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
    <div v-if="detailVisible" class="dialog-overlay" @click.self="closeDetail">
      <div class="dialog dialog--lg">
        <div class="dialog__header">
          <h3>{{ selectedImage?.title || selectedImage?.original_filename }}</h3>
          <button class="dialog__close" @click="closeDetail">
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
          
          <!-- 标题编辑 -->
          <div class="detail-section">
            <label class="detail-section__label">图片标题</label>
            <div class="title-edit">
              <input 
                v-model="editTitle" 
                type="text" 
                class="form-input" 
                placeholder="给图片起个名字（可选）"
                maxlength="200"
                @keyup.enter="saveTitle"
              />
              <button 
                class="btn btn--small" 
                @click="saveTitle" 
                :disabled="savingTitle"
              >
                {{ savingTitle ? '保存中...' : '保存' }}
              </button>
            </div>
            <span class="title-hint">最多200字符，留空则显示原文件名</span>
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
            <div class="link-row">
              <span class="link-row__label">HTML</span>
              <input :value="getHtml(selectedImage)" readonly class="link-row__input" @focus="$event.target.select()" />
              <button class="btn btn--small" @click="copyToClipboard(getHtml(selectedImage))">复制</button>
            </div>
          </div>
          
          <div class="detail-album">
            <span class="detail-album__label">所属相册：</span>
            <select v-model="moveToAlbumId" class="filter-select" @change="moveImage">
              <option :value="null">未分类</option>
              <option v-for="album in albums" :key="album.id" :value="album.id">{{ album.name }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'
import ExportDropdown from '@/components/ExportDropdown.vue'

const { t } = useI18n()
const siteStore = useSiteStore()
const images = ref([])
const albums = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const pageSize = 30  // Larger page size for infinite scroll
const total = ref(0)
const albumFilter = ref(null)
const viewMode = ref('grid')  // 'grid' or 'masonry'
const pageContainer = ref(null)
const loadMoreTrigger = ref(null)

let intersectionObserver = null

// Advanced search state
const showAdvancedSearch = ref(false)
const searchFilters = ref({
  dateFrom: null,
  dateTo: null,
  minWidth: null,
  maxWidth: null,
  minHeight: null,
  maxHeight: null,
})

const detailVisible = ref(false)
const selectedImage = ref(null)
const moveToAlbumId = ref(null)
const editTitle = ref('')
const savingTitle = ref(false)

// Batch mode state
const batchMode = ref(false)
const selectedIds = ref([])
const batchMoveAlbumId = ref(undefined)

const hasMore = computed(() => images.value.length < total.value)

const currentAlbumName = computed(() => {
  if (albumFilter.value === null || albumFilter.value === 0) return ''
  const album = albums.value.find(a => a.id === albumFilter.value)
  return album?.name || ''
})

const hasActiveFilters = computed(() => {
  const f = searchFilters.value
  return f.dateFrom || f.dateTo || f.minWidth || f.maxWidth || f.minHeight || f.maxHeight
})

const activeFilterCount = computed(() => {
  let count = 0
  if (searchFilters.value.dateFrom || searchFilters.value.dateTo) count++
  if (searchFilters.value.minWidth || searchFilters.value.maxWidth || searchFilters.value.minHeight || searchFilters.value.maxHeight) count++
  return count
})

const hasDimensionFilter = computed(() => {
  return searchFilters.value.minWidth || searchFilters.value.maxWidth || searchFilters.value.minHeight || searchFilters.value.maxHeight
})

const formatDateRange = computed(() => {
  const from = searchFilters.value.dateFrom || '...'
  const to = searchFilters.value.dateTo || '...'
  return `${from} ~ ${to}`
})

const formatDimensions = computed(() => {
  const parts = []
  if (searchFilters.value.minWidth) parts.push(`W≥${searchFilters.value.minWidth}`)
  if (searchFilters.value.maxWidth) parts.push(`W≤${searchFilters.value.maxWidth}`)
  if (searchFilters.value.minHeight) parts.push(`H≥${searchFilters.value.minHeight}`)
  if (searchFilters.value.maxHeight) parts.push(`H≤${searchFilters.value.maxHeight}`)
  return parts.join(', ')
})

const isAllSelected = computed(() => {
  return images.value.length > 0 && selectedIds.value.length === images.value.length
})

const isPartialSelected = computed(() => {
  return selectedIds.value.length > 0 && selectedIds.value.length < images.value.length
})

const getAlbumName = (albumId) => {
  const album = albums.value.find(a => a.id === albumId)
  return album?.name || '未知相册'
}

const loadImages = async (reset = false) => {
  if (reset) {
    page.value = 1
    images.value = []
    selectedIds.value = []
  }
  
  if (loading.value || loadingMore.value) return
  if (!reset && !hasMore.value) return
  
  if (reset) {
    loading.value = true
  } else {
    loadingMore.value = true
  }
  
  try {
    const params = { page: page.value, page_size: pageSize }
    if (albumFilter.value !== null) {
      params.album_id = albumFilter.value
    }
    // Add search filters
    if (searchFilters.value.dateFrom) params.date_from = searchFilters.value.dateFrom
    if (searchFilters.value.dateTo) params.date_to = searchFilters.value.dateTo
    if (searchFilters.value.minWidth) params.min_width = searchFilters.value.minWidth
    if (searchFilters.value.maxWidth) params.max_width = searchFilters.value.maxWidth
    if (searchFilters.value.minHeight) params.min_height = searchFilters.value.minHeight
    if (searchFilters.value.maxHeight) params.max_height = searchFilters.value.maxHeight
    
    const response = await api.get('/images', { params })
    
    if (reset) {
      images.value = response.data.items || []
    } else {
      images.value = [...images.value, ...(response.data.items || [])]
    }
    total.value = response.data.total || 0
    page.value++
  } catch (error) {
    console.error(error)
    ElMessage.error(t('error.loadFailed'))
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadAlbums = async () => {
  try {
    const response = await api.get('/albums')
    albums.value = response.data.items || []
  } catch (error) {
    console.error(error)
  }
}

const handleFilterChange = () => {
  loadImages(true)
}

// Switch view mode
const switchViewMode = (mode) => {
  viewMode.value = mode
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

// Search filter methods
const applyPreset = (preset) => {
  switch (preset) {
    case 'hd':
      searchFilters.value.minWidth = 1280
      searchFilters.value.minHeight = 720
      break
    case 'fullhd':
      searchFilters.value.minWidth = 1920
      searchFilters.value.minHeight = 1080
      break
    case '4k':
      searchFilters.value.minWidth = 3840
      searchFilters.value.minHeight = 2160
      break
  }
}

const clearDateFilter = () => {
  searchFilters.value.dateFrom = null
  searchFilters.value.dateTo = null
  applyFilters()
}

const clearDimensionFilter = () => {
  searchFilters.value.minWidth = null
  searchFilters.value.maxWidth = null
  searchFilters.value.minHeight = null
  searchFilters.value.maxHeight = null
  applyFilters()
}

const resetFilters = () => {
  searchFilters.value = {
    dateFrom: null,
    dateTo: null,
    minWidth: null,
    maxWidth: null,
    minHeight: null,
    maxHeight: null,
  }
  applyFilters()
}

const applyFilters = () => {
  loadImages(true)
  showAdvancedSearch.value = false
}

// Batch mode functions
const enterBatchMode = () => {
  batchMode.value = true
  selectedIds.value = []
  batchMoveAlbumId.value = undefined
}

const exitBatchMode = () => {
  batchMode.value = false
  selectedIds.value = []
  batchMoveAlbumId.value = undefined
}

const toggleSelect = (imageId) => {
  const index = selectedIds.value.indexOf(imageId)
  if (index === -1) {
    selectedIds.value.push(imageId)
  } else {
    selectedIds.value.splice(index, 1)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = images.value.map(img => img.id)
  }
}

const handleCardClick = (image) => {
  if (batchMode.value) {
    toggleSelect(image.id)
  } else {
    showDetail(image)
  }
}

const batchMove = async () => {
  if (selectedIds.value.length === 0 || batchMoveAlbumId.value === undefined) return
  
  const targetName = batchMoveAlbumId.value === null 
    ? t('images.uncategorized')
    : albums.value.find(a => a.id === batchMoveAlbumId.value)?.name || ''
  
  try {
    await ElMessageBox.confirm(
      t('images.batchMoveConfirm', { count: selectedIds.value.length, album: targetName }),
      t('common.confirm'),
      { type: 'info' }
    )
    
    await api.put('/images/batch/move', {
      image_ids: selectedIds.value,
      album_id: batchMoveAlbumId.value
    })
    
    ElMessage.success(t('images.batchMoveSuccess', { count: selectedIds.value.length }))
    selectedIds.value = []
    batchMoveAlbumId.value = undefined
    loadImages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(t('error.operationFailed'))
    }
  }
}

const batchDelete = async () => {
  if (selectedIds.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      t('images.batchDeleteConfirm', { count: selectedIds.value.length }),
      t('common.confirm'),
      { type: 'warning' }
    )
    
    await api.delete('/images', {
      params: { image_ids: selectedIds.value }
    })
    
    ElMessage.success(t('images.batchDeleteSuccess', { count: selectedIds.value.length }))
    selectedIds.value = []
    loadImages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(t('error.deleteFailed'))
    }
  }
}

const showDetail = (image) => {
  selectedImage.value = { ...image }
  moveToAlbumId.value = image.album_id
  editTitle.value = image.title || ''
  detailVisible.value = true
}

const closeDetail = () => {
  detailVisible.value = false
  selectedImage.value = null
}

// 如果 URL 已经是完整的（云存储），直接使用；否则拼接 origin
const getFullUrl = (image) => image.url.startsWith('http') ? image.url : window.location.origin + image.url
const getMarkdown = (image) => {
  const title = image.title || image.original_filename
  return `![${title}](${getFullUrl(image)})`
}
const getHtml = (image) => {
  const title = image.title || image.original_filename
  return `<img src="${getFullUrl(image)}" alt="${title}">`
}

const copyUrl = async (image) => {
  await copyToClipboard(getFullUrl(image))
}

const copyToClipboard = async (text) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      ElMessage.success(t('common.copied'))
      return
    }
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

const saveTitle = async () => {
  if (!selectedImage.value) return
  
  savingTitle.value = true
  try {
    const response = await api.put(`/images/${selectedImage.value.id}`, {
      title: editTitle.value.trim()
    })
    
    selectedImage.value.title = response.data.title
    const imageInList = images.value.find(img => img.id === selectedImage.value.id)
    if (imageInList) {
      imageInList.title = response.data.title
    }
    
    ElMessage.success('标题已保存')
  } catch (error) {
    const msg = error.response?.data?.detail || '保存失败'
    ElMessage.error(msg)
  } finally {
    savingTitle.value = false
  }
}

const deleteImage = async (image) => {
  try {
    await ElMessageBox.confirm(t('images.deleteConfirm'), t('common.confirm'), { 
      type: 'warning',
      confirmButtonText: t('common.delete'),
      cancelButtonText: t('common.cancel'),
    })
    await api.delete(`/images/${image.id}`)
    ElMessage.success(t('images.deleteSuccess'))
    loadImages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(t('error.deleteFailed'))
    }
  }
}

const moveImage = async () => {
  if (!selectedImage.value) return
  
  const oldAlbumId = selectedImage.value.album_id
  const newAlbumId = moveToAlbumId.value
  
  if (oldAlbumId === newAlbumId) return
  
  try {
    await api.put(`/images/${selectedImage.value.id}/move`, { album_id: newAlbumId })
    
    selectedImage.value.album_id = newAlbumId
    const imageInList = images.value.find(img => img.id === selectedImage.value.id)
    if (imageInList) {
      imageInList.album_id = newAlbumId
    }
    
    const targetName = newAlbumId 
      ? albums.value.find(a => a.id === newAlbumId)?.name || '指定相册'
      : '未分类'
    ElMessage.success(`已移动到"${targetName}"`)
    
    if (albumFilter.value !== null && albumFilter.value !== newAlbumId) {
      loadImages()
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('移动失败')
    moveToAlbumId.value = oldAlbumId
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
  await loadImages(true)
  loadAlbums()
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
    margin-bottom: 24px;
    
    &-actions {
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

// Header action buttons - unified style
.header-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover {
      opacity: 0.9;
      color: var(--text-inverse);
    }
  }
}

.batch-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  
  &__left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  &__right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  &__count {
    font-size: 13px;
    color: var(--text-secondary);
  }
}

// Batch action buttons - subtle, unified style
.batch-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover:not(:disabled) {
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &--danger {
    color: var(--text-secondary);
    
    &:hover:not(:disabled) {
      color: var(--accent-danger);
      border-color: var(--accent-danger);
      background: var(--accent-danger-bg, rgba(239, 68, 68, 0.08));
    }
  }
  
  &--cancel {
    color: var(--text-tertiary);
    background: transparent;
    border-color: transparent;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-tertiary);
    }
  }
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  
  input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: var(--accent-primary);
  }
}

.checkbox-label {
  font-size: 14px;
  color: var(--text-primary);
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  
  &__left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  &--no-margin {
    margin-bottom: 0;
  }
}

.filter-toggle-btn {
  display: inline-flex;
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
  
  &.is-active {
    background: var(--accent-primary-bg, rgba(59, 130, 246, 0.1));
    color: var(--accent-primary);
  }
}

.filter-badge {
  background: var(--accent-primary);
  color: white;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
}

// Search Panel
.search-panel {
  margin-top: 12px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  
  &__row {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    margin-bottom: 16px;
  }
  
  &__actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 12px;
    border-top: 1px solid var(--border-light);
  }
}

.search-field {
  &__label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-tertiary);
    margin-bottom: 6px;
  }
  
  &__inputs {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  &__sep {
    color: var(--text-tertiary);
    font-size: 12px;
  }
}

.preset-btns {
  display: flex;
  gap: 8px;
}

.preset-btn {
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
    color: var(--text-primary);
  }
}

.action-btns {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
  }
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover {
      opacity: 0.9;
    }
  }
}

// Active Filters
.active-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  margin-bottom: 20px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  font-size: 13px;
  
  &__label {
    color: var(--text-tertiary);
  }
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  
  &__close {
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    font-size: 14px;
    line-height: 1;
    padding: 0 2px;
    
    &:hover {
      color: var(--text-primary);
    }
  }
}

.clear-all-btn {
  background: none;
  border: none;
  color: var(--accent-primary);
  cursor: pointer;
  font-size: 12px;
  margin-left: auto;
  
  &:hover {
    text-decoration: underline;
  }
}

// Slide transition
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.filter-select {
  padding: 8px 32px 8px 12px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-secondary) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpolyline points='6,9 12,15 18,9'/%3E%3C/svg%3E") no-repeat right 10px center;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  appearance: none;
  
  &:focus { outline: none; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.filter-stats {
  font-size: 13px;
  color: var(--text-tertiary);
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

@keyframes spin {
  to { transform: rotate(360deg); }
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
    color: var(--text-tertiary);
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
  
  &--selected {
    outline: 3px solid var(--accent-primary);
    outline-offset: -3px;
  }
  
  img {
    width: 100%;
    height: auto;
    display: block;
  }
  
  &__checkbox {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    
    input[type="checkbox"] {
      width: 20px;
      height: 20px;
      cursor: pointer;
      accent-color: var(--accent-primary);
    }
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
  
  &__album {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 4px;
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

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.image-card {
  position: relative;
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
  
  &--selected {
    outline: 2px solid var(--accent-primary);
    outline-offset: -2px;
  }
  
  &__checkbox {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    
    input[type="checkbox"] {
      width: 20px;
      height: 20px;
      cursor: pointer;
      accent-color: var(--accent-primary);
    }
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
  
  &__album {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 6px;
    font-size: 11px;
    color: var(--text-secondary);
    
    svg { color: var(--text-tertiary); }
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
  }
  
  &--small {
    padding: 6px 12px;
    font-size: 12px;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin {
  animation: spin 1s linear infinite;
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
    position: sticky;
    top: 0;
    background: var(--bg-card);
    z-index: 1;
    
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

.detail-section {
  margin-bottom: 20px;
  
  &__label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }
}

.title-edit {
  display: flex;
  gap: 8px;
  
  .form-input {
    flex: 1;
  }
}

.title-hint {
  display: block;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 6px;
}

.form-input {
  padding: 8px 12px;
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

.detail-links {
  margin-bottom: 20px;
}

.link-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  
  &:last-child { margin-bottom: 0; }
  
  &__label {
    width: 36px;
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

.detail-album {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
  
  &__label {
    font-size: 13px;
    color: var(--text-secondary);
    white-space: nowrap;
  }
  
  .filter-select {
    flex: 1;
  }
}
</style>
