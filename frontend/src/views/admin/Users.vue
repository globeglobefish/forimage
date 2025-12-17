<template>
  <div class="admin-page">
    <h2 class="admin-page__title">{{ $t('admin.users') }}</h2>
    
    <div class="filter-bar">
      <div class="search-box">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input 
          v-model="search" 
          type="text" 
          :placeholder="$t('users.searchPlaceholder')" 
          @keyup.enter="loadUsers"
        />
      </div>
      <select v-model="statusFilter" class="filter-select" @change="loadUsers">
        <option value="">{{ $t('users.allStatus') }}</option>
        <option value="active">{{ $t('users.statusActive') }}</option>
        <option value="pending">{{ $t('users.statusPending') }}</option>
        <option value="disabled">{{ $t('users.statusDisabled') }}</option>
      </select>
      <select v-model="roleFilter" class="filter-select" @change="loadUsers">
        <option value="">{{ $t('users.allRoles') }}</option>
        <option value="user">{{ $t('users.roleUser') }}</option>
        <option value="admin">{{ $t('users.roleAdmin') }}</option>
      </select>
    </div>
    
    <div class="table-card">
      <div v-if="loading" class="loading">
        <div class="loading__spinner"></div>
      </div>
      
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>{{ $t('users.username') }}</th>
            <th>{{ $t('users.email') }}</th>
            <th>{{ $t('users.role') }}</th>
            <th>{{ $t('users.status') }}</th>
            <th>{{ $t('users.lastLoginIP') }}</th>
            <th>{{ $t('users.createdAt') }}</th>
            <th>{{ $t('users.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td class="cell-primary">{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="badge" :class="user.role === 'admin' ? 'badge--primary' : ''">
                {{ user.role === 'admin' ? $t('users.roleAdmin') : $t('users.roleUser') }}
              </span>
            </td>
            <td>
              <span class="badge" :class="getStatusClass(user.status)">
                {{ getStatusText(user.status) }}
              </span>
            </td>
            <td class="cell-muted cell-ip">{{ user.last_login_ip || '-' }}</td>
            <td class="cell-muted">{{ formatDate(user.created_at) }}</td>
            <td>
              <div class="action-btns">
                <button class="action-btn" @click="showEditDialog(user)" :title="$t('common.edit')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button class="action-btn action-btn--danger" @click="deleteUser(user)" :title="$t('common.delete')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3,6 5,6 21,6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="8" class="empty-cell">{{ $t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="total > pageSize" class="table-pagination">
        <span class="table-pagination__info">{{ $t('common.total') }} {{ total }}</span>
        <div class="table-pagination__btns">
          <button :disabled="page <= 1" @click="page--; loadUsers()">{{ $t('common.prev') }}</button>
          <span>{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
          <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; loadUsers()">{{ $t('common.next') }}</button>
        </div>
      </div>
    </div>
    
    <!-- Edit Dialog -->
    <div v-if="editDialogVisible" class="dialog-overlay" @click.self="editDialogVisible = false">
      <div class="dialog">
        <div class="dialog__header">
          <h3>{{ $t('users.editTitle') }}</h3>
          <button class="dialog__close" @click="editDialogVisible = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog__body" v-if="editingUser">
          <div class="form-group">
            <label class="form-label">{{ $t('users.username') }}</label>
            <input :value="editingUser.username" class="form-input" disabled />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('users.email') }}</label>
            <input :value="editingUser.email" class="form-input" disabled />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('users.roleLabel') }}</label>
            <select v-model="editForm.role" class="form-input">
              <option value="user">{{ $t('users.normalUser') }}</option>
              <option value="admin">{{ $t('users.administrator') }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('users.statusLabel') }}</label>
            <select v-model="editForm.status" class="form-input">
              <option value="active">{{ $t('users.activeStatus') }}</option>
              <option value="pending">{{ $t('users.pendingStatus') }}</option>
              <option value="disabled">{{ $t('users.disabledStatus') }}</option>
            </select>
          </div>
        </div>
        <div class="dialog__footer">
          <button class="btn btn--secondary" @click="editDialogVisible = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn--primary" @click="updateUser" :disabled="updating">
            {{ updating ? $t('users.saving') : $t('users.save') }}
          </button>
        </div>
      </div>
    </div>
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
const users = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const search = ref('')
const statusFilter = ref('')
const roleFilter = ref('')

const editDialogVisible = ref(false)
const editingUser = ref(null)
const editForm = reactive({ role: '', status: '' })
const updating = ref(false)

const loadUsers = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (search.value) params.search = search.value
    if (statusFilter.value) params.status = statusFilter.value
    if (roleFilter.value) params.role = roleFilter.value
    
    const response = await api.get('/admin/users', { params })
    users.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const showEditDialog = (user) => {
  editingUser.value = user
  editForm.role = user.role
  editForm.status = user.status
  editDialogVisible.value = true
}

const updateUser = async () => {
  updating.value = true
  try {
    await api.put(`/admin/users/${editingUser.value.id}`, editForm)
    ElMessage.success(t('common.success'))
    editDialogVisible.value = false
    loadUsers()
  } catch (error) {
    console.error(error)
  } finally {
    updating.value = false
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(t('users.deleteConfirm', { name: user.username }), t('common.confirm'), { type: 'warning' })
    await api.delete(`/admin/users/${user.id}`)
    ElMessage.success(t('common.success'))
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const getStatusClass = (status) => {
  const classes = { active: 'badge--success', pending: 'badge--warning', disabled: 'badge--danger' }
  return classes[status] || ''
}

const getStatusText = (status) => {
  const texts = { 
    active: t('users.statusActive'), 
    pending: t('users.statusPending'), 
    disabled: t('users.statusDisabled') 
  }
  return texts[status] || status
}

const formatDate = (date) => {
  return formatDateTime(date, siteStore.timezone())
}

onMounted(() => {
  loadUsers()
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
    padding: 14px 16px;
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
  
  tbody tr:hover { background: var(--bg-secondary); }
}

.badge {
  display: inline-block;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  
  &--primary { background: var(--accent-primary-bg); color: var(--text-primary); }
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

// Dialog styles
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
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-light);
    
    h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0; }
  }
  
  &__close {
    background: none;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    padding: 4px;
    &:hover { color: var(--text-primary); }
  }
  
  &__body { padding: 24px; }
  
  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid var(--border-light);
  }
}

.form-group {
  margin-bottom: 20px;
  &:last-child { margin-bottom: 0; }
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  
  &:focus { outline: none; border-color: var(--border-medium); background: var(--bg-card); }
  &:disabled { opacity: 0.6; }
}

.btn {
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
}
</style>
