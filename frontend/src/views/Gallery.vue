<template>
  <div class="gallery-page">
    <div class="gallery-header">
      <h1 class="gallery-title">{{ $t('gallery.title') }}</h1>
      <p class="gallery-subtitle">{{ $t('gallery.subtitle') }}</p>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <div v-else-if="albums.length === 0" class="empty-state">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21,15 16,10 5,21"/>
      </svg>
      <p>{{ $t('gallery.noAlbums') }}</p>
    </div>

    <div v-else class="album-grid">
      <div
        v-for="album in albums"
        :key="album.id"
        class="album-card"
        @click="$router.push(`/gallery/${album.id}`)"
      >
        <div class="album-card__cover">
          <img 
            v-if="album.cover_image" 
            :src="album.cover_image.url" 
            :alt="album.name"
            loading="lazy"
          />
          <div v-else class="album-card__placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21,15 16,10 5,21"/>
            </svg>
          </div>
        </div>
        <div class="album-card__info">
          <h3 class="album-card__name">{{ album.name }}</h3>
          <p v-if="album.description" class="album-card__desc">{{ album.description }}</p>
          <div class="album-card__meta">
            <span class="album-card__owner">{{ album.owner_name }}</span>
            <span class="album-card__count">{{ $t('gallery.imageCount', { count: album.image_count }) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button 
        class="pagination__btn" 
        :disabled="page === 1"
        @click="changePage(page - 1)"
      >
        {{ $t('common.prev') }}
      </button>
      <span class="pagination__info">{{ page }} / {{ totalPages }}</span>
      <button 
        class="pagination__btn" 
        :disabled="page >= totalPages"
        @click="changePage(page + 1)"
      >
        {{ $t('common.next') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()

const loading = ref(false)
const albums = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12

const totalPages = computed(() => Math.ceil(total.value / pageSize))

const loadAlbums = async () => {
  loading.value = true
  try {
    const response = await api.get('/gallery', {
      params: { page: page.value, page_size: pageSize }
    })
    albums.value = response.data.albums || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Failed to load gallery:', error)
  } finally {
    loading.value = false
  }
}

const changePage = (newPage) => {
  page.value = newPage
  loadAlbums()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  loadAlbums()
})
</script>

<style lang="scss" scoped>
.gallery-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.gallery-header {
  text-align: center;
  margin-bottom: 40px;
}

.gallery-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px;
}

.gallery-subtitle {
  font-size: 16px;
  color: var(--text-tertiary);
  margin: 0;
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
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-tertiary);
  
  svg { 
    margin-bottom: 20px;
    opacity: 0.5;
  }
  
  p { 
    font-size: 16px;
    margin: 0;
  }
}

.album-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.album-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-neu-flat);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-neu-convex);
    
    .album-card__cover img {
      transform: scale(1.05);
    }
  }
  
  &__cover {
    aspect-ratio: 16 / 10;
    overflow: hidden;
    background: var(--bg-secondary);
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s ease;
    }
  }
  
  &__placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-tertiary);
    opacity: 0.5;
  }
  
  &__info {
    padding: 16px;
  }
  
  &__name {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 6px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__desc {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 0 0 12px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--text-tertiary);
  }
  
  &__owner {
    display: flex;
    align-items: center;
    gap: 4px;
    
    &::before {
      content: '@';
    }
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 40px;
  
  &__btn {
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    background: var(--bg-secondary);
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s;
    
    &:hover:not(:disabled) {
      background: var(--bg-tertiary);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  &__info {
    font-size: 14px;
    color: var(--text-secondary);
  }
}
</style>
