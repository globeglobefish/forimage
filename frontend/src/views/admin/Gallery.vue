<template>
  <div class="admin-gallery">
    <div class="page-header">
      <h1>{{ $t('adminGallery.title') }}</h1>
    </div>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic :title="$t('adminGallery.publicAlbums')" :value="stats.total_public_albums" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic :title="$t('adminGallery.publicImages')" :value="stats.total_public_images" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <el-statistic :title="$t('adminGallery.usersWithPublic')" :value="stats.total_users_with_public_albums" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Albums Table -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('adminGallery.publicAlbumList') }}</span>
          <el-switch 
            v-model="publicOnly" 
            :active-text="$t('adminGallery.publicOnly')"
            @change="loadAlbums"
          />
        </div>
      </template>

      <el-table :data="albums" v-loading="loading" stripe>
        <el-table-column prop="name" :label="$t('adminGallery.albumName')" min-width="150">
          <template #default="{ row }">
            <div class="album-name">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_public" type="success" size="small">{{ $t('adminGallery.public') }}</el-tag>
              <el-tag v-else type="info" size="small">{{ $t('adminGallery.private') }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" :label="$t('adminGallery.owner')" width="120">
          <template #default="{ row }">
            <div class="owner-info">
              <span>@{{ row.owner_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column :label="$t('adminGallery.images')" width="120" align="center">
          <template #default="{ row }">
            <span class="text-success">{{ row.approved_count }}</span>
            <span class="text-muted"> / {{ row.image_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('common.createdAt')" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewAlbum(row)">
                {{ $t('common.view') }}
              </el-button>
              <el-button 
                size="small" 
                :type="row.is_public ? 'warning' : 'success'"
                @click="togglePublic(row)"
              >
                {{ row.is_public ? $t('adminGallery.setPrivate') : $t('adminGallery.setPublic') }}
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadAlbums"
        />
      </div>
    </el-card>

    <!-- Album Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentAlbum?.name || $t('adminGallery.albumDetail')"
      width="800px"
    >
      <div v-if="currentAlbum" class="album-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('adminGallery.albumName')">{{ currentAlbum.name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.status')">
            <el-tag :type="currentAlbum.is_public ? 'success' : 'info'">
              {{ currentAlbum.is_public ? $t('adminGallery.public') : $t('adminGallery.private') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.owner')">
            @{{ currentAlbum.owner_name }} ({{ currentAlbum.owner_email }})
          </el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.description')" :span="2">
            {{ currentAlbum.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.totalImages')">{{ currentAlbum.total_images }}</el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.approvedImages')">
            <span class="text-success">{{ currentAlbum.approved_count }}</span>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.pendingImages')">
            <span class="text-warning">{{ currentAlbum.pending_count }}</span>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('adminGallery.rejectedImages')">
            <span class="text-danger">{{ currentAlbum.rejected_count }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <h4 class="images-title">{{ $t('adminGallery.imagesInAlbum') }}</h4>
        <div class="images-grid">
          <div 
            v-for="image in currentAlbum.images" 
            :key="image.id" 
            class="image-item"
            :class="{ 'image-item--rejected': image.status === 'rejected' }"
          >
            <img :src="image.url" :alt="image.filename" />
            <el-tag 
              :type="getStatusType(image.status)" 
              size="small" 
              class="image-status"
            >
              {{ getStatusLabel(image.status) }}
            </el-tag>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button 
          :type="currentAlbum?.is_public ? 'warning' : 'success'"
          @click="togglePublicFromDetail"
        >
          {{ currentAlbum?.is_public ? $t('adminGallery.setPrivate') : $t('adminGallery.setPublic') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'

const { t } = useI18n()
const siteStore = useSiteStore()

const loading = ref(false)
const albums = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const publicOnly = ref(true)
const detailDialogVisible = ref(false)
const currentAlbum = ref(null)

const stats = reactive({
  total_public_albums: 0,
  total_public_images: 0,
  total_users_with_public_albums: 0,
})

const loadStats = async () => {
  try {
    const response = await api.get('/admin/gallery/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadAlbums = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/gallery', {
      params: {
        page: page.value,
        page_size: pageSize,
        public_only: publicOnly.value,
      }
    })
    albums.value = response.data.albums || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('Failed to load albums:', error)
    ElMessage.error(t('adminGallery.loadError'))
  } finally {
    loading.value = false
  }
}

const viewAlbum = async (album) => {
  try {
    const response = await api.get(`/admin/gallery/${album.id}`)
    currentAlbum.value = response.data
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error(t('adminGallery.loadDetailError'))
  }
}

const togglePublic = async (album) => {
  const newStatus = !album.is_public
  const action = newStatus ? t('adminGallery.setPublic') : t('adminGallery.setPrivate')
  
  try {
    await ElMessageBox.confirm(
      t('adminGallery.toggleConfirm', { name: album.name, action }),
      t('common.confirm'),
      { type: 'warning' }
    )
    
    await api.put(`/admin/gallery/${album.id}/toggle-public`, { is_public: newStatus })
    ElMessage.success(t('adminGallery.toggleSuccess'))
    loadAlbums()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('adminGallery.toggleError'))
    }
  }
}

const togglePublicFromDetail = async () => {
  if (!currentAlbum.value) return
  
  const newStatus = !currentAlbum.value.is_public
  
  try {
    await api.put(`/admin/gallery/${currentAlbum.value.id}/toggle-public`, { is_public: newStatus })
    currentAlbum.value.is_public = newStatus
    ElMessage.success(t('adminGallery.toggleSuccess'))
    loadAlbums()
    loadStats()
  } catch (error) {
    ElMessage.error(t('adminGallery.toggleError'))
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return formatDateTime(dateStr, siteStore.timezone())
}

const getStatusType = (status) => {
  const types = { approved: 'success', pending: 'warning', rejected: 'danger' }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    approved: t('adminGallery.statusApproved'),
    pending: t('adminGallery.statusPending'),
    rejected: t('adminGallery.statusRejected'),
  }
  return labels[status] || status
}

onMounted(() => {
  loadStats()
  loadAlbums()
})
</script>

<style scoped>
.admin-gallery {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.album-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-info {
  font-size: 13px;
}

.text-success { color: #67c23a; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
.text-muted { color: #909399; }

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.album-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.images-title {
  margin: 20px 0 12px;
  font-size: 14px;
  font-weight: 600;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-item--rejected {
  opacity: 0.5;
}

.image-status {
  position: absolute;
  bottom: 4px;
  left: 4px;
}
</style>
