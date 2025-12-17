<template>
  <div class="admin-page">
    <h2 class="admin-page__title">{{ $t('backup.title') }}</h2>
    
    <div class="settings-layout">
      <!-- Sidebar Navigation -->
      <nav class="settings-nav">
        <button 
          v-for="tab in tabs" 
          :key="tab.key"
          class="settings-nav__item"
          :class="{ 'is-active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span class="settings-nav__icon" v-html="tab.icon"></span>
          <span class="settings-nav__text">{{ tab.label }}</span>
        </button>
      </nav>
      
      <!-- Content Area -->
      <div class="settings-content">
        <!-- Overview Tab -->
        <div v-show="activeTab === 'overview'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('backup.overview') }}</h3>
            <p class="section-desc">{{ $t('backup.overviewDesc') }}</p>
          </div>
          
          <div class="settings-card">
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-item__value">{{ dashboard.total_nodes }}</span>
                <span class="stat-item__label">{{ $t('backup.totalNodes') }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-item__value">{{ dashboard.enabled_nodes }}</span>
                <span class="stat-item__label">{{ $t('backup.enabledNodes') }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-item__value">{{ dashboard.total_files_backed_up }}</span>
                <span class="stat-item__label">{{ $t('backup.totalFiles') }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-item__value">{{ formatBytes(dashboard.total_bytes_backed_up) }}</span>
                <span class="stat-item__label">{{ $t('backup.totalSize') }}</span>
              </div>
            </div>
          </div>
          
          <div class="settings-card">
            <h4 class="config-title">{{ $t('backup.quickActions') }}</h4>
            <div class="action-buttons">
              <button class="btn btn--primary" @click="showAddDialog">
                <span>+</span> {{ $t('backup.addNode') }}
              </button>
              <button class="btn btn--secondary" @click="fetchDashboard">{{ $t('backup.refresh') }}</button>
            </div>
          </div>
          
          <div class="settings-card">
            <h4 class="config-title">{{ $t('backup.tips') }}</h4>
            <div class="tips-list">
              <div class="tip-row">
                <span class="tip-badge">M</span>
                <div class="tip-text">
                  <strong>{{ $t('backup.strategy.manual') }}</strong>
                  <span>{{ $t('backup.manualTip') }}</span>
                </div>
              </div>
              <div class="tip-row">
                <span class="tip-badge">R</span>
                <div class="tip-text">
                  <strong>{{ $t('backup.strategy.realtime') }}</strong>
                  <span>{{ $t('backup.realtimeTipLong') }}</span>
                </div>
              </div>
              <div class="tip-row">
                <span class="tip-badge">S</span>
                <div class="tip-text">
                  <strong>{{ $t('backup.strategy.scheduled') }}</strong>
                  <span>{{ $t('backup.scheduledTip') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Nodes Tab -->
        <div v-show="activeTab === 'nodes'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('backup.nodeList') }}</h3>
            <p class="section-desc">{{ $t('backup.nodeListDesc') }}</p>
          </div>
          
          <div class="settings-card">
            <div class="card-header">
              <span class="card-header__title">{{ $t('backup.configuredNodes') }} ({{ nodes.length }})</span>
              <button class="btn btn--primary btn--sm" @click="showAddDialog">+ {{ $t('backup.addNode') }}</button>
            </div>
            
            <div v-if="loading" class="loading-state">
              <div class="spinner"></div>
              <span>{{ $t('common.loading') }}</span>
            </div>
            
            <div v-else-if="nodes.length === 0" class="empty-state">
              <p>{{ $t('backup.noNodes') }}</p>
              <button class="btn btn--primary" @click="showAddDialog">{{ $t('backup.addFirstNode') }}</button>
            </div>
            
            <div v-else class="nodes-list">
              <div v-for="node in nodes" :key="node.id" class="node-card">
                <div class="node-card__header">
                  <div class="node-card__info">
                    <span class="node-card__name">{{ node.name }}</span>
                    <span class="node-card__badge">{{ node.protocol.toUpperCase() }}</span>
                    <span class="node-card__badge node-card__badge--muted">{{ $t(`backup.strategy.${node.sync_strategy}`) }}</span>
                  </div>
                  <label class="switch">
                    <input type="checkbox" v-model="node.is_enabled" @change="toggleNode(node)" />
                    <span class="switch__slider"></span>
                  </label>
                </div>
                
                <div class="node-card__stats">
                  <div class="node-stat">
                    <span class="node-stat__label">{{ $t('backup.files') }}</span>
                    <span class="node-stat__value">{{ node.total_files || 0 }}</span>
                  </div>
                  <div class="node-stat">
                    <span class="node-stat__label">{{ $t('backup.size') }}</span>
                    <span class="node-stat__value">{{ formatBytes(node.total_bytes || 0) }}</span>
                  </div>
                  <div class="node-stat">
                    <span class="node-stat__label">{{ $t('backup.lastSync') }}</span>
                    <span class="node-stat__value">{{ node.last_sync_at ? formatDate(node.last_sync_at) : '-' }}</span>
                  </div>
                </div>
                
                <div class="node-card__actions">
                  <button class="btn btn--sm btn--secondary" @click="testConnection(node)" :disabled="node.testing">
                    {{ node.testing ? '...' : $t('backup.test') }}
                  </button>
                  <button class="btn btn--sm btn--primary" @click="triggerBackup(node)" :disabled="node.backing">
                    {{ node.backing ? '...' : $t('backup.backup') }}
                  </button>
                  <button class="btn btn--sm btn--secondary" @click="showNodeStatus(node)">{{ $t('backup.viewStatus') }}</button>
                  <button class="btn btn--sm btn--secondary" @click="editNode(node)">{{ $t('common.edit') }}</button>
                  <button class="btn btn--sm btn--text btn--danger" @click="deleteNode(node)">{{ $t('common.delete') }}</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Logs Tab -->
        <div v-show="activeTab === 'logs'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('backup.backupLogs') }}</h3>
            <p class="section-desc">{{ $t('backup.logsDesc') }}</p>
          </div>
          
          <div class="settings-card">
            <div class="card-header">
              <div class="filter-row">
                <select v-model="logFilter.node_id" class="form-input form-select form-select--sm" @change="fetchLogs">
                  <option :value="null">{{ $t('backup.allNodes') }}</option>
                  <option v-for="node in nodes" :key="node.id" :value="node.id">{{ node.name }}</option>
                </select>
                <select v-model="logFilter.task_type" class="form-input form-select form-select--sm" @change="fetchLogs">
                  <option :value="null">{{ $t('backup.allTypes') }}</option>
                  <option value="backup">{{ $t('backup.taskTypes.backup') }}</option>
                  <option value="realtime">{{ $t('backup.taskTypes.realtime') }}</option>
                  <option value="test">{{ $t('backup.taskTypes.test') }}</option>
                </select>
                <select v-model="logFilter.status" class="form-input form-select form-select--sm" @change="fetchLogs">
                  <option :value="null">{{ $t('backup.allStatuses') }}</option>
                  <option value="success">{{ $t('backup.taskStatuses.success') }}</option>
                  <option value="partial">{{ $t('backup.taskStatuses.partial') }}</option>
                  <option value="failed">{{ $t('backup.taskStatuses.failed') }}</option>
                </select>
              </div>
              <button class="btn btn--sm btn--secondary" @click="fetchLogs">{{ $t('backup.refresh') }}</button>
            </div>
            
            <div v-if="logsLoading" class="loading-state"><div class="spinner"></div></div>
            
            <div v-else-if="logs.length === 0" class="empty-state">
              <p>{{ $t('backup.noLogs') }}</p>
            </div>
            
            <div v-else class="logs-table">
              <table>
                <thead>
                  <tr>
                    <th>{{ $t('backup.nodeName') }}</th>
                    <th>{{ $t('backup.logTaskType') }}</th>
                    <th>{{ $t('backup.status') }}</th>
                    <th>{{ $t('backup.filesSuccess') }}/{{ $t('backup.filesFailed') }}</th>
                    <th>{{ $t('backup.bytesTransferred') }}</th>
                    <th>{{ $t('backup.time') }}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in logs" :key="log.id">
                    <td>{{ log.node_name || '-' }}</td>
                    <td>{{ getTaskTypeLabel(log.task_type) }}</td>
                    <td><span class="status-badge" :class="'status-badge--' + log.status">{{ getTaskStatusLabel(log.status) }}</span></td>
                    <td><span class="text-success">{{ log.files_success ?? 0 }}</span> / <span :class="{ 'text-danger': log.files_failed > 0 }">{{ log.files_failed ?? 0 }}</span></td>
                    <td>{{ formatBytes(log.bytes_transferred) }}</td>
                    <td>{{ formatDate(log.created_at) }}</td>
                    <td>
                      <button class="btn btn--sm btn--text" @click="showLogDetail(log)">{{ $t('backup.viewDetail') }}</button>
                      <button class="btn btn--sm btn--text btn--danger" @click="deleteLog(log)">{{ $t('common.delete') }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div v-if="logsPagination.total > logsPagination.pageSize" class="pagination">
              <button class="btn btn--sm btn--secondary" :disabled="logsPagination.page <= 1" @click="changePage(logsPagination.page - 1)">{{ $t('admin.prevPage') }}</button>
              <span class="pagination__info">{{ logsPagination.page }} / {{ Math.ceil(logsPagination.total / logsPagination.pageSize) }}</span>
              <button class="btn btn--sm btn--secondary" :disabled="logsPagination.page >= Math.ceil(logsPagination.total / logsPagination.pageSize)" @click="changePage(logsPagination.page + 1)">{{ $t('admin.nextPage') }}</button>
            </div>
          </div>
        </div>

        <!-- Maintenance Tab -->
        <div v-show="activeTab === 'maintenance'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('backup.maintenance') }}</h3>
            <p class="section-desc">{{ $t('backup.maintenanceDesc') }}</p>
          </div>
          
          <div class="settings-card">
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('backup.selectNode') }}</span>
              </label>
              <select v-model="selectedMaintenanceNode" class="form-input form-select">
                <option :value="null">{{ $t('backup.selectNodePlaceholder') }}</option>
                <option v-for="node in nodes" :key="node.id" :value="node.id">{{ node.name }}</option>
              </select>
            </div>
          </div>
          
          <template v-if="selectedMaintenanceNode">
            <div class="settings-card">
              <h4 class="config-title">{{ $t('backup.retryFailed') }}</h4>
              <p class="config-desc">{{ $t('backup.retryFailedDesc') }}</p>
              <button class="btn btn--secondary" @click="retryFailedFiles">{{ $t('backup.retryFailed') }}</button>
            </div>
            
            <div class="settings-card">
              <h4 class="config-title">{{ $t('backup.cleanupDeleted') }}</h4>
              <p class="config-desc">{{ $t('backup.cleanupDeletedDesc') }}</p>
              <button class="btn btn--secondary" @click="cleanupDeletedRecords">{{ $t('backup.cleanupDeleted') }}</button>
            </div>
            
            <div class="settings-card">
              <h4 class="config-title">{{ $t('backup.syncStatus') }}</h4>
              <p class="config-desc">{{ $t('backup.syncStatusDesc') }}</p>
              <button class="btn btn--secondary" @click="syncFileStatus">{{ $t('backup.syncStatus') }}</button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Add/Edit Node Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('backup.editNode') : $t('backup.addNode')" width="600px">
      <el-form :model="nodeForm" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item :label="$t('backup.nodeName')" prop="name">
          <el-input v-model="nodeForm.name" :placeholder="$t('backup.nodeNamePlaceholder')" />
        </el-form-item>
        
        <el-form-item :label="$t('backup.protocol')" prop="protocol">
          <el-select v-model="nodeForm.protocol" @change="onProtocolChange" :disabled="isEdit" style="width: 100%">
            <el-option value="ftp" label="FTP" />
            <el-option value="sftp" label="SFTP" />
            <el-option value="s3" label="S3" />
            <el-option value="webdav" label="WebDAV" />
          </el-select>
        </el-form-item>

        <!-- FTP/SFTP Config -->
        <template v-if="nodeForm.protocol === 'ftp' || nodeForm.protocol === 'sftp'">
          <el-divider>{{ $t('backup.connectionConfig') }}</el-divider>
          <el-form-item :label="$t('backup.host')"><el-input v-model="nodeForm.connection_config.host" placeholder="ftp.example.com" /></el-form-item>
          <el-form-item :label="$t('backup.port')"><el-input-number v-model="nodeForm.connection_config.port" :min="1" :max="65535" style="width: 100%" /></el-form-item>
          <el-form-item :label="$t('backup.username')"><el-input v-model="nodeForm.connection_config.username" /></el-form-item>
          <el-form-item :label="$t('backup.password')"><el-input v-model="nodeForm.connection_config.password" type="password" show-password :placeholder="isEdit ? $t('backup.passwordPlaceholder') : ''" /></el-form-item>
          <el-form-item :label="$t('backup.remotePath')"><el-input v-model="nodeForm.connection_config.remote_path" placeholder="/backup/images" /></el-form-item>
        </template>

        <!-- S3 Config -->
        <template v-if="nodeForm.protocol === 's3'">
          <el-divider>{{ $t('backup.connectionConfig') }}</el-divider>
          <el-form-item :label="$t('backup.s3Provider')">
            <el-select v-model="nodeForm.connection_config.provider" @change="onS3ProviderChange" style="width: 100%">
              <el-option value="custom" :label="$t('backup.s3Providers.custom')" />
              <el-option value="aws" label="AWS S3" />
              <el-option value="r2" label="Cloudflare R2" />
              <el-option value="minio" label="MinIO" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('backup.endpoint')"><el-input v-model="nodeForm.connection_config.endpoint" :placeholder="getS3EndpointPlaceholder()" /></el-form-item>
          <el-form-item :label="$t('backup.accessKey')"><el-input v-model="nodeForm.connection_config.access_key" :placeholder="isEdit ? $t('backup.passwordPlaceholder') : ''" /></el-form-item>
          <el-form-item :label="$t('backup.secretKey')"><el-input v-model="nodeForm.connection_config.secret_key" type="password" show-password :placeholder="isEdit ? $t('backup.passwordPlaceholder') : ''" /></el-form-item>
          <el-form-item :label="$t('backup.bucketName')"><el-input v-model="nodeForm.connection_config.bucket_name" /></el-form-item>
          <el-form-item :label="$t('backup.region')"><el-input v-model="nodeForm.connection_config.region" :placeholder="getS3RegionPlaceholder()" /></el-form-item>
          <el-form-item :label="$t('backup.prefix')"><el-input v-model="nodeForm.connection_config.prefix" placeholder="backup/images" /></el-form-item>
        </template>

        <!-- WebDAV Config -->
        <template v-if="nodeForm.protocol === 'webdav'">
          <el-divider>{{ $t('backup.connectionConfig') }}</el-divider>
          <el-form-item :label="$t('backup.url')"><el-input v-model="nodeForm.connection_config.url" placeholder="https://webdav.example.com" /></el-form-item>
          <el-form-item :label="$t('backup.username')"><el-input v-model="nodeForm.connection_config.username" /></el-form-item>
          <el-form-item :label="$t('backup.password')"><el-input v-model="nodeForm.connection_config.password" type="password" show-password :placeholder="isEdit ? $t('backup.passwordPlaceholder') : ''" /></el-form-item>
          <el-form-item :label="$t('backup.remotePath')"><el-input v-model="nodeForm.connection_config.remote_path" placeholder="/backup/images" /></el-form-item>
        </template>

        <el-divider>{{ $t('backup.syncSettings') }}</el-divider>
        
        <el-form-item :label="$t('backup.syncStrategy')">
          <el-select v-model="nodeForm.sync_strategy" style="width: 100%">
            <el-option value="manual" :label="$t('backup.strategy.manual')" />
            <el-option value="realtime" :label="$t('backup.strategy.realtime')" />
            <el-option value="scheduled" :label="$t('backup.strategy.scheduled')" />
          </el-select>
        </el-form-item>

        <template v-if="nodeForm.sync_strategy === 'scheduled'">
          <el-form-item :label="$t('backup.scheduleType')">
            <el-select v-model="scheduleType" @change="onScheduleTypeChange" style="width: 100%">
              <el-option value="daily" :label="$t('backup.scheduleTypes.daily')" />
              <el-option value="weekly" :label="$t('backup.scheduleTypes.weekly')" />
              <el-option value="custom" :label="$t('backup.scheduleTypes.custom')" />
            </el-select>
          </el-form-item>
          
          <el-form-item :label="$t('backup.scheduleTime')" v-if="scheduleType === 'daily' || scheduleType === 'weekly'">
            <el-time-select v-model="scheduleTime" :start="'00:00'" :step="'01:00'" :end="'23:00'" @change="updateScheduleCron" style="width: 100%" />
          </el-form-item>
          
          <el-form-item :label="$t('backup.scheduleDay')" v-if="scheduleType === 'weekly'">
            <el-select v-model="scheduleDay" @change="updateScheduleCron" style="width: 100%">
              <el-option :value="0" :label="$t('backup.weekdays.sunday')" />
              <el-option :value="1" :label="$t('backup.weekdays.monday')" />
              <el-option :value="2" :label="$t('backup.weekdays.tuesday')" />
              <el-option :value="3" :label="$t('backup.weekdays.wednesday')" />
              <el-option :value="4" :label="$t('backup.weekdays.thursday')" />
              <el-option :value="5" :label="$t('backup.weekdays.friday')" />
              <el-option :value="6" :label="$t('backup.weekdays.saturday')" />
            </el-select>
          </el-form-item>
          
          <el-form-item :label="$t('backup.cronExpression')" v-if="scheduleType === 'custom'">
            <el-input v-model="nodeForm.schedule_cron" placeholder="0 2 * * *" />
          </el-form-item>
        </template>

        <el-form-item :label="$t('backup.maxConcurrent')">
          <el-input-number v-model="nodeForm.max_concurrent" :min="1" :max="10" style="width: 100%" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveNode" :loading="saving">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- Node Status Dialog -->
    <el-dialog v-model="statusDialogVisible" :title="$t('backup.nodeStatus')" width="500px">
      <div v-if="currentNodeStatus" class="status-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('backup.nodeName')" :span="2">{{ currentNodeStatus.nodeName }}</el-descriptions-item>
          <el-descriptions-item :label="$t('backup.totalImages')">{{ currentNodeStatus.total_images }}</el-descriptions-item>
          <el-descriptions-item :label="$t('backup.untracked')">{{ currentNodeStatus.untracked }}</el-descriptions-item>
          <el-descriptions-item :label="$t('backup.statusSynced')">{{ currentNodeStatus.synced?.count || 0 }}</el-descriptions-item>
          <el-descriptions-item :label="$t('backup.statusPending')">{{ currentNodeStatus.pending?.count || 0 }}</el-descriptions-item>
          <el-descriptions-item :label="$t('backup.statusFailed')">{{ currentNodeStatus.failed?.count || 0 }}</el-descriptions-item>
          <el-descriptions-item :label="$t('backup.statusDeleted')">{{ currentNodeStatus.deleted?.count || 0 }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="statusDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- Log Detail Dialog -->
    <el-dialog v-model="logDetailVisible" :title="$t('backup.logDetail')" width="600px">
      <el-descriptions :column="2" border v-if="currentLog">
        <el-descriptions-item :label="$t('backup.nodeName')">{{ currentLog.node_name || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.logTaskType')">{{ getTaskTypeLabel(currentLog.task_type) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.status')">{{ getTaskStatusLabel(currentLog.status) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.duration')">{{ currentLog.duration_seconds ? `${currentLog.duration_seconds}s` : '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.filesTotal')">{{ currentLog.files_total ?? 0 }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.bytesTransferred')">{{ formatBytes(currentLog.bytes_transferred) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.filesSuccess')">{{ currentLog.files_success ?? 0 }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.filesFailed')">{{ currentLog.files_failed ?? 0 }}</el-descriptions-item>
        <el-descriptions-item :label="$t('backup.startTime')" :span="2">{{ currentLog.started_at ? formatDate(currentLog.started_at) : '-' }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="currentLog && currentLog.error_details" class="error-box">
        <h4>{{ $t('backup.errorDetails') }}</h4>
        <pre>{{ formatErrorDetails(currentLog.error_details) }}</pre>
      </div>
      <template #footer>
        <el-button @click="logDetailVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>


<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'

const { t } = useI18n()
const siteStore = useSiteStore()

const activeTab = ref('overview')
const tabs = computed(() => [
  { key: 'overview', label: t('backup.overview'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>' },
  { key: 'nodes', label: t('backup.nodeList'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/></svg>' },
  { key: 'logs', label: t('backup.backupLogs'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' },
  { key: 'maintenance', label: t('backup.maintenance'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
])

const loading = ref(false)
const saving = ref(false)
const logsLoading = ref(false)
const dialogVisible = ref(false)
const logDetailVisible = ref(false)
const statusDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentLog = ref(null)
const currentNodeStatus = ref(null)
const selectedMaintenanceNode = ref(null)

const nodes = ref([])
const logs = ref([])
const dashboard = ref({ total_nodes: 0, enabled_nodes: 0, total_files_backed_up: 0, total_bytes_backed_up: 0 })

const logFilter = reactive({ node_id: null, task_type: null, status: null })
const logsPagination = reactive({ page: 1, pageSize: 20, total: 0 })

const nodeForm = reactive({
  id: null, name: '', protocol: 'ftp', sync_strategy: 'manual', schedule_cron: '', max_concurrent: 3, connection_config: {}
})

const scheduleType = ref('daily')
const scheduleTime = ref('02:00')
const scheduleDay = ref(0)

const formRules = {
  name: [{ required: true, message: t('backup.nameRequired'), trigger: 'blur' }],
  protocol: [{ required: true, message: t('backup.protocolRequired'), trigger: 'change' }]
}

const fetchNodes = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/backup/nodes')
    nodes.value = response.data.nodes.map(node => ({ ...node, testing: false, backing: false }))
  } catch (error) {
    ElMessage.error(t('backup.fetchError'))
  } finally {
    loading.value = false
  }
}

const fetchDashboard = async () => {
  try {
    const response = await api.get('/admin/backup/dashboard')
    dashboard.value = response.data
  } catch (error) {
    console.error('Failed to fetch dashboard:', error)
  }
}

const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const params = { page: logsPagination.page, page_size: logsPagination.pageSize, ...logFilter }
    Object.keys(params).forEach(key => params[key] === null && delete params[key])
    const response = await api.get('/admin/backup/logs', { params })
    logs.value = response.data.logs || []
    logsPagination.total = response.data.total || 0
  } catch (error) {
    console.error('Failed to fetch logs:', error)
    logs.value = []
  } finally {
    logsLoading.value = false
  }
}

const changePage = (page) => { logsPagination.page = page; fetchLogs() }

const showAddDialog = () => {
  isEdit.value = false
  Object.assign(nodeForm, { id: null, name: '', protocol: 'ftp', sync_strategy: 'manual', schedule_cron: '', max_concurrent: 3, connection_config: { port: 21 } })
  scheduleType.value = 'daily'; scheduleTime.value = '02:00'; scheduleDay.value = 0
  dialogVisible.value = true
}

const editNode = (node) => {
  isEdit.value = true
  const config = { ...node.connection_config_masked }
  const sensitiveFields = ['password', 'secret_key', 'private_key', 'access_key']
  sensitiveFields.forEach(field => { if (config[field]) config[field] = '' })
  Object.assign(nodeForm, { id: node.id, name: node.name, protocol: node.protocol, sync_strategy: node.sync_strategy, schedule_cron: node.schedule_cron || '', max_concurrent: node.max_concurrent, connection_config: config })
  parseScheduleCron(node.schedule_cron)
  dialogVisible.value = true
}

const saveNode = async () => {
  try { await formRef.value.validate() } catch { return }
  saving.value = true
  try {
    const data = { name: nodeForm.name, protocol: nodeForm.protocol, sync_strategy: nodeForm.sync_strategy, schedule_cron: nodeForm.sync_strategy === 'scheduled' ? nodeForm.schedule_cron : null, max_concurrent: nodeForm.max_concurrent, connection_config: nodeForm.connection_config }
    if (isEdit.value) { await api.put(`/admin/backup/nodes/${nodeForm.id}`, data); ElMessage.success(t('backup.updateSuccess')) }
    else { await api.post('/admin/backup/nodes', data); ElMessage.success(t('backup.createSuccess')) }
    dialogVisible.value = false; fetchNodes(); fetchDashboard()
  } catch (error) { ElMessage.error(error.response?.data?.detail || t('backup.saveError')) }
  finally { saving.value = false }
}

const deleteNode = async (node) => {
  try {
    await ElMessageBox.confirm(t('backup.deleteConfirm', { name: node.name }), t('common.warning'), { type: 'warning' })
    await api.delete(`/admin/backup/nodes/${node.id}`)
    ElMessage.success(t('backup.deleteSuccess')); fetchNodes(); fetchDashboard()
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('backup.deleteError')) }
}

const toggleNode = async (node) => {
  try { await api.put(`/admin/backup/nodes/${node.id}`, { is_enabled: node.is_enabled }); ElMessage.success(node.is_enabled ? t('backup.enabled') : t('backup.disabled')) }
  catch (error) { node.is_enabled = !node.is_enabled; ElMessage.error(t('backup.toggleError')) }
}

const testConnection = async (node) => {
  node.testing = true
  try {
    const response = await api.post(`/admin/backup/nodes/${node.id}/test`)
    if (response.data.success) ElMessage.success(t('backup.testSuccess', { latency: response.data.latency_ms?.toFixed(0) }))
    else ElMessage.error(response.data.message)
    fetchLogs()
  } catch (error) { ElMessage.error(t('backup.testError')) }
  finally { node.testing = false }
}

const triggerBackup = async (node) => {
  try { await ElMessageBox.confirm(t('backup.backupConfirm', { name: node.name }), t('backup.startBackup'), { type: 'info' }) } catch { return }
  node.backing = true; ElMessage.info(t('backup.backupStarted'))
  try {
    const response = await api.post(`/admin/backup/nodes/${node.id}/backup`)
    if (response.data.status === 'success') ElMessage.success(t('backup.backupSuccess', { success: response.data.files_completed, total: response.data.files_total }))
    else ElMessage.warning(response.data.message || t('backup.backupPartial'))
    fetchNodes(); fetchDashboard(); fetchLogs()
  } catch (error) { ElMessage.error(error.response?.data?.detail || t('backup.backupError')) }
  finally { node.backing = false }
}

const showNodeStatus = async (node) => {
  try {
    const response = await api.get(`/admin/backup/nodes/${node.id}/status`)
    currentNodeStatus.value = { ...response.data, nodeName: node.name }
    statusDialogVisible.value = true
  } catch (error) { ElMessage.error(t('backup.fetchStatusError')) }
}

const showLogDetail = (log) => { currentLog.value = log; logDetailVisible.value = true }

const deleteLog = async (log) => {
  try {
    await ElMessageBox.confirm(t('backup.deleteLogConfirm'), t('common.warning'), { type: 'warning' })
    await api.delete(`/admin/backup/logs/${log.id}`)
    ElMessage.success(t('backup.deleteLogSuccess')); fetchLogs(); fetchDashboard()
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('backup.deleteLogError')) }
}

const getSelectedNode = () => nodes.value.find(n => n.id === selectedMaintenanceNode.value)

const retryFailedFiles = async () => {
  const node = getSelectedNode(); if (!node) return
  try {
    await ElMessageBox.confirm(t('backup.retryConfirm', { name: node.name }), t('backup.retryFailed'), { type: 'info' })
    const response = await api.post(`/admin/backup/nodes/${node.id}/retry-failed`)
    ElMessage.success(t('backup.retrySuccess', { count: response.data.reset_count })); fetchNodes(); fetchDashboard()
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('backup.retryError')) }
}

const cleanupDeletedRecords = async () => {
  const node = getSelectedNode(); if (!node) return
  try {
    await ElMessageBox.confirm(t('backup.cleanupConfirm', { name: node.name }), t('backup.cleanupDeleted'), { type: 'warning' })
    const response = await api.post(`/admin/backup/nodes/${node.id}/cleanup`)
    ElMessage.success(t('backup.cleanupSuccess', { count: response.data.deleted_count })); fetchNodes(); fetchDashboard()
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('backup.cleanupError')) }
}

const syncFileStatus = async () => {
  const node = getSelectedNode(); if (!node) return
  try {
    await ElMessageBox.confirm(t('backup.syncConfirm', { name: node.name }), t('backup.syncStatus'), { type: 'info' })
    const response = await api.post(`/admin/backup/nodes/${node.id}/sync-status`)
    ElMessage.success(t('backup.syncSuccess', { count: response.data.orphaned_count })); fetchNodes(); fetchDashboard()
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('backup.syncError')) }
}

const onScheduleTypeChange = () => { if (scheduleType.value !== 'custom') updateScheduleCron() }
const updateScheduleCron = () => {
  const hour = parseInt(scheduleTime.value.split(':')[0])
  if (scheduleType.value === 'daily') nodeForm.schedule_cron = `0 ${hour} * * *`
  else if (scheduleType.value === 'weekly') nodeForm.schedule_cron = `0 ${hour} * * ${scheduleDay.value}`
}

const parseScheduleCron = (cron) => {
  if (!cron) { scheduleType.value = 'daily'; scheduleTime.value = '02:00'; scheduleDay.value = 0; return }
  const parts = cron.trim().split(/\s+/)
  if (parts.length !== 5) { scheduleType.value = 'custom'; return }
  const [, hour, dayOfMonth, month, dayOfWeek] = parts
  if (dayOfMonth === '*' && month === '*') {
    scheduleTime.value = `${parseInt(hour).toString().padStart(2, '0')}:00`
    if (dayOfWeek === '*') scheduleType.value = 'daily'
    else { scheduleType.value = 'weekly'; scheduleDay.value = parseInt(dayOfWeek) }
  } else scheduleType.value = 'custom'
}

const onProtocolChange = () => {
  const defaults = { ftp: { port: 21, remote_path: '/' }, sftp: { port: 22, remote_path: '/' }, s3: { provider: 'custom', region: 'us-east-1' }, webdav: { remote_path: '/' } }
  nodeForm.connection_config = defaults[nodeForm.protocol] || {}
}

const onS3ProviderChange = () => {
  const presets = { aws: { region: 'us-east-1' }, r2: { region: 'auto' }, minio: { region: 'us-east-1' }, custom: { region: 'us-east-1' } }
  nodeForm.connection_config.region = presets[nodeForm.connection_config.provider]?.region || 'us-east-1'
}

const getS3EndpointPlaceholder = () => {
  const p = { aws: 'https://s3.amazonaws.com', r2: 'https://<account_id>.r2.cloudflarestorage.com', minio: 'https://minio.example.com:9000', custom: 'https://s3.example.com' }
  return p[nodeForm.connection_config.provider] || p.custom
}
const getS3RegionPlaceholder = () => {
  const p = { aws: 'us-east-1', r2: 'auto', minio: 'us-east-1', custom: 'us-east-1' }
  return p[nodeForm.connection_config.provider] || p.custom
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'], i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr) => dateStr ? formatDateTime(dateStr, siteStore.timezone()) : '-'
const formatErrorDetails = (details) => { if (!details) return ''; try { const p = JSON.parse(details); return Array.isArray(p) ? p.join('\n') : details } catch { return details } }

const getTaskTypeLabel = (taskType) => {
  const labels = { backup: t('backup.taskTypes.backup'), realtime: t('backup.taskTypes.realtime'), restore: t('backup.taskTypes.restore'), sync: t('backup.taskTypes.sync'), test: t('backup.taskTypes.test') }
  return labels[taskType] || taskType || '-'
}
const getTaskStatusLabel = (status) => {
  const labels = { running: t('backup.taskStatuses.running'), success: t('backup.taskStatuses.success'), partial: t('backup.taskStatuses.partial'), failed: t('backup.taskStatuses.failed'), cancelled: t('backup.taskStatuses.cancelled') }
  return labels[status] || status || '-'
}

onMounted(() => { fetchNodes(); fetchDashboard(); fetchLogs() })
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

.settings-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: sticky;
  top: 88px;
  align-self: start;
  
  &__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s;
    text-align: left;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-secondary);
    }
    
    &.is-active {
      color: var(--text-primary);
      background: var(--bg-card);
      box-shadow: var(--shadow-sm);
    }
  }
  
  &__icon {
    display: flex;
    color: inherit;
    opacity: 0.7;
  }
}

.settings-content {
  min-width: 0;
}

.settings-section {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px;
}

.section-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin: 0;
}

.settings-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-neu-flat);
  margin-bottom: 16px;
}

.config-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 16px;
}

.config-desc {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: -8px 0 16px;
}

// Stats
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  text-align: center;
  
  &__value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  &__label {
    font-size: 13px;
    color: var(--text-tertiary);
    margin-top: 4px;
  }
}

// Buttons
.action-buttons {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover {
      opacity: 0.9;
    }
  }
  
  &--secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    
    &:hover {
      background: var(--bg-tertiary);
    }
  }
  
  &--text {
    background: transparent;
    color: var(--text-secondary);
    padding: 6px 10px;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-secondary);
    }
  }
  
  &--danger {
    color: var(--color-danger);
  }
  
  &--sm {
    padding: 6px 12px;
    font-size: 13px;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// Tips
.tips-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.tip-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.tip-text {
  strong {
    display: block;
    font-size: 14px;
    color: var(--text-primary);
    margin-bottom: 2px;
  }
  
  span {
    font-size: 13px;
    color: var(--text-tertiary);
    line-height: 1.4;
  }
}

// Card Header
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
  
  &__title {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
  }
}

// Nodes
.nodes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.node-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  &__info {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  &__name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  &__badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    
    &--muted {
      color: var(--text-tertiary);
    }
  }
  
  &__stats {
    display: flex;
    gap: 24px;
    margin-bottom: 12px;
  }
  
  &__actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}

.node-stat {
  &__label {
    font-size: 12px;
    color: var(--text-tertiary);
    display: block;
  }
  
  &__value {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

// Switch
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  
  input {
    opacity: 0;
    width: 0;
    height: 0;
    
    &:checked + .switch__slider {
      background: var(--accent-primary);
      
      &::before {
        transform: translateX(20px);
      }
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

// Filter
.filter-row {
  display: flex;
  gap: 12px;
}

.form-select--sm {
  padding: 8px 12px;
  font-size: 13px;
  min-width: 140px;
}

// Logs Table
.logs-table {
  overflow-x: auto;
  
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  
  th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-light);
  }
  
  th {
    font-weight: 500;
    color: var(--text-secondary);
    background: var(--bg-secondary);
  }
  
  td {
    color: var(--text-primary);
  }
  
  tr:hover td {
    background: var(--bg-secondary);
  }
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  
  &--success {
    background: var(--bg-secondary);
    color: var(--color-success);
  }
  
  &--failed {
    background: var(--bg-secondary);
    color: var(--color-danger);
  }
  
  &--partial {
    background: var(--bg-secondary);
    color: var(--color-warning);
  }
  
  &--running {
    background: var(--bg-secondary);
    color: var(--accent-primary);
  }
}

.text-success {
  color: var(--color-success);
}

.text-danger {
  color: var(--color-danger);
}

// Pagination
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
  
  &__info {
    font-size: 13px;
    color: var(--text-tertiary);
  }
}

// Form
.form-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
  align-items: start;
  margin-bottom: 20px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.label-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
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
  
  &::placeholder {
    color: var(--text-tertiary);
  }
  
  &:focus {
    outline: none;
    border-color: var(--border-medium);
    background: var(--bg-card);
  }
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpolyline points='6,9 12,15 18,9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
  cursor: pointer;
}

// States
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 20px;
  color: var(--text-tertiary);
  
  p {
    margin: 0 0 16px 0;
  }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-light);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// Error box
.error-box {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  
  h4 {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 8px;
  }
  
  pre {
    font-size: 12px;
    color: var(--text-tertiary);
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
  }
}

// Responsive
@media (max-width: 800px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }
  
  .settings-nav {
    flex-direction: row;
    flex-wrap: wrap;
    position: static;
    gap: 8px;
    
    &__item {
      padding: 10px 14px;
    }
    
    &__text {
      display: none;
    }
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-row {
    flex-wrap: wrap;
  }
  
  .node-card__stats {
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .node-card__actions {
    flex-wrap: wrap;
  }
}
</style>
