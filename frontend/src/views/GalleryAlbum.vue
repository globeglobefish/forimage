<template>
  <div class="gallery-album-page" ref="pageContainer">
    <div v-if="loading && images.length === 0" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <template v-else-if="album">
      <div class="album-header">
        <button class="back-btn" @click="$router.push('/gallery')">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          {{ $t('gallery.backToGallery') }}
        </button>
        
        <div class="album-info">
          <h1 class="album-title">{{ album.name }}</h1>
          <p v-if="album.description" class="album-desc">{{ album.description }}</p>
          <div class="album-meta">
            <span class="album-owner">@{{ album.owner_name }}</span>
            <span class="album-count">{{ $t('gallery.totalImages', { count: totalImages }) }}</span>
          </div>
        </div>
      </div>
      
      <!-- Sort Options Bar -->
      <div class="sort-bar">
        <div class="sort-bar__left">
          <span class="sort-bar__label">{{ $t('sort.sortBy') }}:</span>
          <select v-model="currentSort" class="sort-select" @change="handleSortChange">
            <option value="created_at_desc">{{ $t('sort.dateNewest') }}</option>
            <option value="created_at_asc">{{ $t('sort.dateOldest') }}</option>
            <option value="file_size_desc">{{ $t('sort.sizelargest') }}</option>
            <option value="file_size_asc">{{ $t('sort.sizeSmallest') }}</option>
          </select>
          
          <ExportDropdown 
            :images="images"
            :album-id="albumId"
            :album-name="album.name"
            :disabled="totalImages === 0"
            :is-gallery="true"
          />
        </div>
        <div class="sort-bar__right">
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'masonry' }"
            @click="switchViewMode('masonry')"
            :title="$t('gallery.masonryView')"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/>
              <rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>
            </svg>
          </button>
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'grid' }"
            @click="switchViewMode('grid')"
            :title="$t('gallery.gridView')"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
          </button>
          <button 
            class="view-toggle" 
            :class="{ 'is-active': viewMode === 'list' }"
            @click="switchViewMode('list')"
            :title="$t('gallery.listView')"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
          </button>
        </div>
      </div>

      <div v-if="images.length === 0 && !loading" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21,15 16,10 5,21"/>
        </svg>
        <p>{{ $t('gallery.noImages') }}</p>
      </div>

      <!-- Masonry View (Waterfall) with Infinite Scroll -->
      <div v-else-if="viewMode === 'masonry'" class="masonry-grid" ref="masonryContainer">
        <div
          v-for="image in images"
          :key="image.id"
          class="masonry-item"
          @click="openLightbox(image)"
        >
          <img 
            :src="image.url" 
            :alt="image.title || image.filename" 
            loading="lazy"
          />
          <div class="masonry-item__overlay">
            <span v-if="image.title" class="masonry-item__title">{{ image.title }}</span>
            <div class="masonry-item__meta">
              <span v-if="image.width && image.height">{{ image.width }} × {{ image.height }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="image-grid">
        <div
          v-for="image in images"
          :key="image.id"
          class="image-card"
          @click="openLightbox(image)"
        >
          <div class="image-card__thumb">
            <img :src="image.url" :alt="image.title || image.filename" loading="lazy" />
          </div>
          <div class="image-card__info" v-if="image.title">
            <span class="image-card__title">{{ image.title }}</span>
          </div>
        </div>
      </div>
      
      <!-- List View -->
      <div v-else class="image-list">
        <div
          v-for="image in images"
          :key="image.id"
          class="image-list-item"
          @click="openLightbox(image)"
        >
          <div class="image-list-item__thumb">
            <img :src="image.url" :alt="image.title || image.filename" loading="lazy" />
          </div>
          <div class="image-list-item__info">
            <span class="image-list-item__title">{{ image.title || image.filename }}</span>
            <div class="image-list-item__meta">
              <span v-if="image.width && image.height">{{ image.width }} × {{ image.height }}</span>
              <span v-if="image.file_size">{{ formatSize(image.file_size) }}</span>
              <span>{{ formatDate(image.created_at) }}</span>
            </div>
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

    <div v-else class="error-state">
      <p>{{ $t('gallery.albumNotFound') }}</p>
      <button class="btn btn--primary" @click="$router.push('/gallery')">
        {{ $t('gallery.backToGallery') }}
      </button>
    </div>

    <!-- Lightbox -->
    <div v-if="lightboxImage" class="lightbox" @click="closeLightbox">
      <button class="lightbox__close" @click="closeLightbox">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
      <img :src="lightboxImage.url" :alt="lightboxImage.title || lightboxImage.filename" @click.stop />
      <div class="lightbox__info">
        <div v-if="lightboxImage.title" class="lightbox__title">{{ lightboxImage.title }}</div>
        <div class="lightbox__meta">
          <span v-if="lightboxImage.width && lightboxImage.height">{{ lightboxImage.width }} × {{ lightboxImage.height }}</span>
          <span v-if="lightboxImage.file_size">{{ formatSize(lightboxImage.file_size) }}</span>
        </div>
        <a :href="lightboxImage.url" target="_blank" class="lightbox__link">
          {{ $t('gallery.openOriginal') }}
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'
import api from '@/api'
import ExportDropdown from '@/components/ExportDropdown.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()

const albumId = route.params.id
const loading = ref(false)
const loadingMore = ref(false)
const album = ref(null)
const images = ref([])
const page = ref(1)
const pageSize = 30  // Larger page size for infinite scroll
const totalImages = ref(0)
const lightboxImage = ref(null)
const viewMode = ref('grid')
const currentSort = ref('created_at_desc')
const masonryContainer = ref(null)
const pageContainer = ref(null)
const loadMoreTrigger = ref(null)

let intersectionObserver = null

const hasMore = computed(() => images.value.length < totalImages.value)

// Parse sort preference string
const parseSortPreference = (pref) => {
  if (!pref) return { sortBy: 'created_at', sortOrder: 'desc' }
  const parts = pref.split('_')
  if (parts.length >= 2) {
    const sortOrder = parts[parts.length - 1]
    const sortBy = parts.slice(0, -1).join('_')
    return { sortBy, sortOrder }
  }
  return { sortBy: 'created_at', sortOrder: 'desc' }
}

// Load album info
const loadAlbum = async () => {
  try {
    const response = await api.get(`/gallery/${albumId}`, {
      params: { page: 1, page_size: 1 }
    })
    album.value = {
      id: response.data.id,
      name: response.data.name,
      description: response.data.description,
      owner_name: response.data.owner_name,
      created_at: response.data.created_at
    }
    totalImages.value = response.data.total_images
  } catch (error) {
    console.error('Failed to load album:', error)
    album.value = null
  }
}

// Load images with pagination
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
    const params = { page: page.value, page_size: pageSize }
    
    // Apply sort
    const { sortBy, sortOrder } = parseSortPreference(currentSort.value)
    params.sort_by = sortBy
    params.sort_order = sortOrder
    
    const response = await api.get(`/gallery/${albumId}`, { params })
    
    if (reset) {
      images.value = response.data.images || []
      totalImages.value = response.data.total_images
      album.value = {
        id: response.data.id,
        name: response.data.name,
        description: response.data.description,
        owner_name: response.data.owner_name,
        created_at: response.data.created_at
      }
    } else {
      images.value = [...images.value, ...(response.data.images || [])]
    }
    
    page.value++
  } catch (error) {
    console.error('Failed to load images:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// Handle sort change
const handleSortChange = () => {
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

const formatSize = (bytes) => {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const formatDate = (date) => {
  if (!date) return ''
  return formatDateTime(date, siteStore.timezone())
}

const openLightbox = (image) => {
  lightboxImage.value = image
  document.body.style.overflow = 'hidden'
}

const closeLightbox = () => {
  lightboxImage.value = null
  document.body.style.overflow = ''
}

onMounted(async () => {
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
.gallery-album-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 80px;
  
  &__spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border-light);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    
    &--small {
      width: 24px;
      height: 24px;
      border-width: 2px;
    }
  }
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 30px;
  color: var(--text-tertiary);
  font-size: 14px;
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 20px;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
}

.album-header {
  margin-bottom: 32px;
}

.album-info {
  text-align: center;
}

.album-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.album-desc {
  font-size: 15px;
  color: var(--text-tertiary);
  margin: 0 0 16px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.album-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  font-size: 14px;
  color: var(--text-tertiary);
}

.album-owner {
  color: var(--accent-primary);
}

.empty-state, .error-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
  
  svg { margin-bottom: 16px; opacity: 0.5; }
  p { margin: 0 0 20px; font-size: 15px; }
}

.sort-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  
  &__left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  &__label {
    font-size: 13px;
    color: var(--text-tertiary);
  }
  
  &__right {
    display: flex;
    gap: 4px;
  }
}

.sort-select {
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  
  &:focus {
    outline: none;
  }
}

.view-toggle {
  width: 36px;
  height: 36px;
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
    font-size: 14px;
    font-weight: 500;
    color: white;
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 4px;
  }
  
  &__meta {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
  }
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.image-card {
  overflow: hidden;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: var(--shadow-sm);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    
    .image-card__thumb img {
      transform: scale(1.05);
    }
  }
  
  &__thumb {
    aspect-ratio: 1;
    overflow: hidden;
    background: var(--bg-secondary);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s ease;
    }
  }
  
  &__info {
    padding: 10px 12px;
  }
  
  &__title {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.image-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-list-item {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: var(--shadow-sm);
  
  &:hover {
    background: var(--bg-secondary);
    box-shadow: var(--shadow-md);
  }
  
  &__thumb {
    width: 80px;
    height: 80px;
    flex-shrink: 0;
    border-radius: var(--radius-md);
    overflow: hidden;
    background: var(--bg-secondary);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  &__info {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
  }
  
  &__title {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__meta {
    display: flex;
    gap: 16px;
    font-size: 13px;
    color: var(--text-tertiary);
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
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover { opacity: 0.9; }
  }
  
  &--secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    
    &:hover { background: var(--bg-tertiary); }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
}

.download-btn {
  margin-top: 16px;
}

.spin {
  animation: spin 1s linear infinite;
}

// Lightbox
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  
  &__close {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 50%;
    color: white;
    cursor: pointer;
    transition: background 0.2s;
    
    &:hover {
      background: rgba(255, 255, 255, 0.2);
    }
  }
  
  img {
    max-width: 90vw;
    max-height: 80vh;
    object-fit: contain;
    border-radius: var(--radius-md);
  }
  
  &__info {
    margin-top: 16px;
    text-align: center;
  }
  
  &__title {
    font-size: 18px;
    font-weight: 600;
    color: white;
    margin-bottom: 8px;
  }
  
  &__meta {
    display: flex;
    justify-content: center;
    gap: 16px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 12px;
  }
  
  &__link {
    color: rgba(255, 255, 255, 0.8);
    text-decoration: none;
    font-size: 14px;
    
    &:hover {
      color: white;
      text-decoration: underline;
    }
  }
}
</style>
