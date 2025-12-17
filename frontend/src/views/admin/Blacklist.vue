<template>
  <div class="admin-page">
    <h2 class="admin-page__title">{{ $t('admin.securityManagement') }}</h2>
    
    <!-- Stats Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-card__icon stat-card__icon--danger">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ stats.active_bans }}</div>
          <div class="stat-card__label">{{ $t('admin.activeBans') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-card__icon stat-card__icon--warning">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ stats.violations_24h }}</div>
          <div class="stat-card__label">{{ $t('admin.violations24h') }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-card__icon stat-card__icon--info">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ stats.pending_appeals }}</div>
          <div class="stat-card__label">{{ $t('admin.pendingAppeals') }}</div>
        </div>
      </div>
    </div>
    
    <!-- Tabs -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key" 
        :class="['tab', { 'tab--active': activeTab === tab.key }]"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
        <span v-if="tab.key === 'appeals' && stats.pending_appeals > 0" class="tab__badge">
          {{ stats.pending_appeals }}
        </span>
      </button>
    </div>
    
    <!-- Settings Tab -->
    <div v-show="activeTab === 'settings'" class="tab-content">
      <div class="settings-card">
        <h4 class="section-title">{{ $t('admin.guestRateLimit') }}</h4>
        <div class="form-row form-row--inline">
          <div class="form-col">
            <label class="form-label">{{ $t('admin.perMinute') }}</label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_limit_guest_per_minute" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
          <div class="form-col">
            <label class="form-label">{{ $t('admin.perHour') }}</label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_limit_guest_per_hour" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
          <div class="form-col">
            <label class="form-label">{{ $t('admin.perDay') }}</label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_limit_guest_per_day" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
        </div>
        
        <div class="form-divider"></div>
        <h4 class="section-title">{{ $t('admin.userRateLimit') }}</h4>
        <div class="form-row form-row--inline">
          <div class="form-col">
            <label class="form-label">{{ $t('admin.perMinute') }}</label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_limit_user_per_minute" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
          <div class="form-col">
            <label class="form-label">{{ $t('admin.perHour') }}</label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_limit_user_per_hour" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
          <div class="form-col">
            <label class="form-label">{{ $t('admin.perDay') }}</label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_limit_user_per_day" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
        </div>
        
        <div class="form-divider"></div>
        <h4 class="section-title">{{ $t('admin.autoBan') }}</h4>
        
        <div class="form-row form-row--switch">
          <div class="form-row__label">
            <span class="label-text">{{ $t('admin.enableAutoBan') }}</span>
            <span class="label-hint">{{ $t('admin.autoBanHint') }}</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="securitySettings.auto_ban_enabled" />
            <span class="switch__slider"></span>
          </label>
        </div>
        
        <template v-if="securitySettings.auto_ban_enabled">
          <div class="form-row">
            <label class="form-label">
              <span class="label-text">{{ $t('admin.auditFailThreshold') }}</span>
              <span class="label-hint">{{ $t('admin.auditFailThresholdHint') }}</span>
            </label>
            <div class="input-group">
              <input v-model.number="securitySettings.audit_fail_threshold" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
          
          <div class="form-row">
            <label class="form-label">
              <span class="label-text">{{ $t('admin.rateExceedThreshold') }}</span>
              <span class="label-hint">{{ $t('admin.rateExceedThresholdHint') }}</span>
            </label>
            <div class="input-group">
              <input v-model.number="securitySettings.rate_exceed_threshold" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.times') }}</span>
            </div>
          </div>
          
          <div class="form-row">
            <label class="form-label">
              <span class="label-text">{{ $t('admin.tempBanDuration') }}</span>
              <span class="label-hint">{{ $t('admin.tempBanDurationHint') }}</span>
            </label>
            <div class="input-group">
              <input v-model.number="securitySettings.temp_ban_duration" type="number" class="form-input" min="1" />
              <span class="input-suffix">{{ $t('admin.minutes') }}</span>
            </div>
          </div>
        </template>
        
        <div class="form-divider"></div>
        <h4 class="section-title">{{ $t('admin.ipDetection') }}</h4>
        
        <div class="form-row form-row--switch">
          <div class="form-row__label">
            <span class="label-text">{{ $t('admin.trustProxy') }}</span>
            <span class="label-hint">{{ $t('admin.trustProxyHint') }}</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="securitySettings.trust_proxy" />
            <span class="switch__slider"></span>
          </label>
        </div>
        
        <div class="form-row" v-if="securitySettings.trust_proxy">
          <label class="form-label">
            <span class="label-text">{{ $t('admin.realIpHeader') }}</span>
            <span class="label-hint">{{ $t('admin.realIpHeaderHint') }}</span>
          </label>
          <select v-model="securitySettings.real_ip_header" class="form-input form-select">
            <option value="X-Forwarded-For">X-Forwarded-For (Standard Proxy)</option>
            <option value="X-Real-IP">X-Real-IP (Nginx)</option>
            <option value="CF-Connecting-IP">CF-Connecting-IP (Cloudflare)</option>
            <option value="True-Client-IP">True-Client-IP (Cloudflare Enterprise)</option>
          </select>
        </div>
        
        <div class="ip-header-hint" v-if="securitySettings.trust_proxy">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <span v-html="$t('admin.ipHeaderHint')"></span>
        </div>
        
        <div class="form-divider"></div>
        <h4 class="section-title">{{ $t('admin.loginSecurity') }}</h4>
        
        <div class="form-row">
          <label class="form-label">
            <span class="label-text">{{ $t('admin.loginFailLimitLabel') }}</span>
            <span class="label-hint">{{ $t('admin.loginFailLimitHintText') }}</span>
          </label>
          <div class="input-group">
            <input v-model.number="securitySettings.rate_limit_login_attempts" type="number" class="form-input" min="1" />
            <span class="input-suffix">{{ $t('admin.timesUnit') }}</span>
          </div>
        </div>
        
        <div class="form-actions">
          <button class="btn btn--primary" @click="saveSecuritySettings" :disabled="savingSettings">
            <template v-if="savingSettings">{{ $t('admin.saving') }}</template>
            <template v-else>{{ $t('admin.saveSettings') }}</template>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Blacklist Tab -->
    <div v-show="activeTab === 'blacklist'" class="tab-content">
      <div class="filter-bar">
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input v-model="blacklistSearch" type="text" :placeholder="$t('admin.searchIpOrReasonPlaceholder')" @keyup.enter="blacklistPage = 1; loadBlacklist()" />
        </div>
        <label class="checkbox-label">
          <input type="checkbox" v-model="activeOnly" @change="blacklistPage = 1; loadBlacklist()" />
          <span>{{ $t('admin.showActiveOnlyLabel') }}</span>
        </label>
        <button class="btn btn--primary" @click="showAddBanDialog">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          {{ $t('admin.manualBanAction') }}
        </button>
      </div>
      
      <div class="table-card">
        <div v-if="loadingBlacklist" class="loading"><div class="loading__spinner"></div></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>{{ $t('admin.ipOrUserLabel') }}</th>
              <th>{{ $t('admin.reasonLabel') }}</th>
              <th>{{ $t('admin.typeLabel') }}</th>
              <th>{{ $t('admin.statusLabel') }}</th>
              <th>{{ $t('admin.violationCountLabel') }}</th>
              <th>{{ $t('admin.expiresOrLiftedLabel') }}</th>
              <th>{{ $t('admin.actionsLabel') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ban in blacklist" :key="ban.id" :class="{ 'row-lifted': ban.lifted_at }">
              <td class="cell-primary">
                <div v-if="ban.ip_address">{{ ban.ip_address }}</div>
                <div v-if="ban.username" class="cell-sub">{{ $t('admin.userLabel') }}: {{ ban.username }}</div>
              </td>
              <td>{{ ban.reason }}</td>
              <td>
                <span class="badge" :class="ban.ban_type === 'PERMANENT' ? 'badge--danger' : 'badge--warning'">
                  {{ ban.ban_type === 'PERMANENT' ? $t('admin.permanent') : $t('admin.temporary') }}
                </span>
              </td>
              <td>
                <span v-if="ban.lifted_at" class="badge badge--success">{{ $t('admin.lifted') }}</span>
                <span v-else-if="ban.is_active" class="badge badge--danger">{{ $t('common.active') }}</span>
                <span v-else class="badge badge--muted">{{ $t('admin.expired') }}</span>
              </td>
              <td>{{ ban.violation_count }}</td>
              <td class="cell-muted">
                <template v-if="ban.lifted_at">
                  <div>{{ formatDate(ban.lifted_at) }}</div>
                  <div class="cell-sub">{{ ban.lift_reason }}</div>
                </template>
                <template v-else-if="ban.ban_type === 'PERMANENT'">{{ $t('admin.neverExpires') }}</template>
                <template v-else>{{ formatDate(ban.expires_at) }}</template>
              </td>
              <td>
                <div v-if="!ban.lifted_at && ban.is_active" class="action-btns">
                  <button class="action-btn" @click="extendBan(ban)" :title="$t('admin.extendAction')" v-if="ban.ban_type !== 'PERMANENT'">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>
                    </svg>
                  </button>
                  <button class="action-btn action-btn--danger" @click="removeBan(ban)" :title="$t('admin.liftAction')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M18 6L6 18"/><path d="M6 6l12 12"/>
                    </svg>
                  </button>
                </div>
                <span v-else class="cell-muted">-</span>
              </td>
            </tr>
            <tr v-if="blacklist.length === 0">
              <td colspan="7" class="empty-cell">{{ $t('admin.noRecords') }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="blacklistTotal > pageSize" class="table-pagination">
          <span class="table-pagination__info">{{ $t('admin.totalItemsLabel', { count: blacklistTotal }) }}</span>
          <div class="table-pagination__btns">
            <button :disabled="blacklistPage <= 1" @click="blacklistPage--; loadBlacklist()">{{ $t('admin.prevPage') }}</button>
            <span>{{ $t('admin.pageInfo', { current: blacklistPage, total: Math.ceil(blacklistTotal / pageSize) }) }}</span>
            <button :disabled="blacklistPage >= Math.ceil(blacklistTotal / pageSize)" @click="blacklistPage++; loadBlacklist()">{{ $t('admin.nextPage') }}</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Violations Tab -->
    <div v-show="activeTab === 'violations'" class="tab-content">
      <div class="filter-bar">
        <select v-model="violationTypeFilter" class="filter-select" @change="violationsPage = 1; loadViolations()">
          <option value="">{{ $t('admin.allTypesOption') }}</option>
          <option value="audit_failed">{{ $t('admin.auditFailedType') }}</option>
          <option value="rate_limit_exceeded">{{ $t('admin.rateLimitExceededType') }}</option>
        </select>
      </div>
      
      <div class="table-card">
        <div v-if="loadingViolations" class="loading"><div class="loading__spinner"></div></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>{{ $t('admin.ipAddressLabel') }}</th>
              <th>{{ $t('admin.userLabel') }}</th>
              <th>{{ $t('admin.typeLabel') }}</th>
              <th>{{ $t('admin.detailsLabel') }}</th>
              <th>{{ $t('common.time') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="v in violations" :key="v.id">
              <td class="cell-primary">{{ v.ip_address }}</td>
              <td>{{ v.username || '-' }}</td>
              <td>
                <span class="badge" :class="v.violation_type === 'audit_failed' ? 'badge--danger' : 'badge--warning'">
                  {{ v.violation_type === 'audit_failed' ? $t('admin.auditFailedType') : $t('admin.rateLimitExceededType') }}
                </span>
              </td>
              <td>
                <button class="btn btn--text btn--sm" @click="showViolationDetail(v)">
                  {{ $t('admin.viewDetailsAction') }}
                </button>
              </td>
              <td class="cell-muted">{{ formatDate(v.created_at) }}</td>
            </tr>
            <tr v-if="violations.length === 0">
              <td colspan="5" class="empty-cell">{{ $t('admin.noViolations') }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="violationsTotal > pageSize" class="table-pagination">
          <span class="table-pagination__info">{{ $t('admin.totalItemsLabel', { count: violationsTotal }) }}</span>
          <div class="table-pagination__btns">
            <button :disabled="violationsPage <= 1" @click="violationsPage--; loadViolations()">{{ $t('admin.prevPage') }}</button>
            <span>{{ $t('admin.pageInfo', { current: violationsPage, total: Math.ceil(violationsTotal / pageSize) }) }}</span>
            <button :disabled="violationsPage >= Math.ceil(violationsTotal / pageSize)" @click="violationsPage++; loadViolations()">{{ $t('admin.nextPage') }}</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Appeals Tab -->
    <div v-show="activeTab === 'appeals'" class="tab-content">
      <div class="filter-bar">
        <select v-model="appealStatusFilter" class="filter-select" @change="appealsPage = 1; loadAppeals()">
          <option value="">{{ $t('admin.allStatusOption') }}</option>
          <option value="PENDING">{{ $t('admin.pendingStatus') }}</option>
          <option value="APPROVED">{{ $t('admin.approvedStatus') }}</option>
          <option value="REJECTED">{{ $t('admin.rejectedStatus') }}</option>
        </select>
      </div>
      
      <div class="table-card">
        <div v-if="loadingAppeals" class="loading"><div class="loading__spinner"></div></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>{{ $t('admin.userLabel') }}</th>
              <th>{{ $t('appeal.appealReason') }}</th>
              <th>{{ $t('admin.statusLabel') }}</th>
              <th>{{ $t('admin.submitTime') }}</th>
              <th>{{ $t('admin.actionsLabel') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="appeal in appeals" :key="appeal.id">
              <td class="cell-primary">{{ appeal.username }}</td>
              <td>{{ appeal.reason }}</td>
              <td>
                <span class="badge" :class="getAppealStatusClass(appeal.status)">
                  {{ getAppealStatusText(appeal.status) }}
                </span>
              </td>
              <td class="cell-muted">{{ formatDate(appeal.created_at) }}</td>
              <td>
                <div v-if="appeal.status.toUpperCase() === 'PENDING'" class="action-btns">
                  <button class="action-btn action-btn--success" @click="handleAppeal(appeal, 'approved')" :title="$t('admin.approveAction')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20,6 9,17 4,12"/>
                    </svg>
                  </button>
                  <button class="action-btn action-btn--danger" @click="handleAppeal(appeal, 'rejected')" :title="$t('admin.rejectAction')">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
                <span v-else class="cell-muted">{{ appeal.admin_response || '-' }}</span>
              </td>
            </tr>
            <tr v-if="appeals.length === 0">
              <td colspan="5" class="empty-cell">{{ $t('admin.noAppeals') }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="appealsTotal > pageSize" class="table-pagination">
          <span class="table-pagination__info">{{ $t('admin.totalItemsLabel', { count: appealsTotal }) }}</span>
          <div class="table-pagination__btns">
            <button :disabled="appealsPage <= 1" @click="appealsPage--; loadAppeals()">{{ $t('admin.prevPage') }}</button>
            <span>{{ $t('admin.pageInfo', { current: appealsPage, total: Math.ceil(appealsTotal / pageSize) }) }}</span>
            <button :disabled="appealsPage >= Math.ceil(appealsTotal / pageSize)" @click="appealsPage++; loadAppeals()">{{ $t('admin.nextPage') }}</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Audit Logs Tab -->
    <div v-show="activeTab === 'audit'" class="tab-content">
      <div class="filter-bar">
        <select v-model="auditActionFilter" class="filter-select" @change="auditPage = 1; loadAuditLogs()">
          <option value="">{{ $t('admin.allActionsOption') }}</option>
          <option value="login">{{ $t('admin.loginAction') }}</option>
          <option value="upload">{{ $t('admin.uploadAction') }}</option>
          <option value="delete">{{ $t('admin.deleteAction') }}</option>
          <option value="admin_action">{{ $t('admin.adminActionType') }}</option>
        </select>
        <select v-model="auditResourceFilter" class="filter-select" @change="auditPage = 1; loadAuditLogs()">
          <option value="">{{ $t('admin.allResourcesOption') }}</option>
          <option value="user">{{ $t('admin.userResource') }}</option>
          <option value="image">{{ $t('admin.imageResource') }}</option>
          <option value="album">{{ $t('admin.albumResource') }}</option>
          <option value="settings">{{ $t('admin.settingsResource') }}</option>
        </select>
      </div>
      
      <div class="table-card">
        <div v-if="loadingAudit" class="loading"><div class="loading__spinner"></div></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>{{ $t('admin.action') }}</th>
              <th>{{ $t('admin.resource') }}</th>
              <th>{{ $t('admin.userLabel') }}</th>
              <th>{{ $t('admin.ipAddressLabel') }}</th>
              <th>{{ $t('admin.statusLabel') }}</th>
              <th>{{ $t('common.time') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in auditLogs" :key="log.id">
              <td class="cell-primary">{{ log.action }}</td>
              <td>{{ log.resource_type || '-' }}{{ log.resource_id ? ' #' + log.resource_id : '' }}</td>
              <td>{{ log.user_id || $t('admin.guestUser') }}</td>
              <td class="cell-muted">{{ log.ip_address }}</td>
              <td>
                <span class="badge" :class="log.status === 'success' ? 'badge--success' : 'badge--danger'">
                  {{ log.status === 'success' ? $t('admin.successStatus') : $t('admin.failedStatus') }}
                </span>
              </td>
              <td class="cell-muted">{{ formatDate(log.created_at) }}</td>
            </tr>
            <tr v-if="auditLogs.length === 0">
              <td colspan="6" class="empty-cell">{{ $t('admin.noAuditLogs') }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="auditTotal > pageSize" class="table-pagination">
          <span class="table-pagination__info">{{ $t('admin.totalItemsLabel', { count: auditTotal }) }}</span>
          <div class="table-pagination__btns">
            <button :disabled="auditPage <= 1" @click="auditPage--; loadAuditLogs()">{{ $t('admin.prevPage') }}</button>
            <span>{{ $t('admin.pageInfo', { current: auditPage, total: Math.ceil(auditTotal / pageSize) }) }}</span>
            <button :disabled="auditPage >= Math.ceil(auditTotal / pageSize)" @click="auditPage++; loadAuditLogs()">{{ $t('admin.nextPage') }}</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add Ban Dialog -->
    <div v-if="addBanDialogVisible" class="dialog-overlay" @click.self="addBanDialogVisible = false">
      <div class="dialog">
        <div class="dialog__header">
          <h3>{{ $t('admin.addBanTitle') }}</h3>
          <button class="dialog__close" @click="addBanDialogVisible = false">&times;</button>
        </div>
        <div class="dialog__body">
          <div class="form-group">
            <label class="form-label">{{ $t('admin.ipAddressLabel') }}</label>
            <input v-model="newBan.ip_address" type="text" class="form-input" :placeholder="$t('admin.optionalField')" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('admin.userIdLabel') }}</label>
            <input v-model.number="newBan.user_id" type="number" class="form-input" :placeholder="$t('admin.optionalField')" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('admin.banReason') }} *</label>
            <input v-model="newBan.reason" type="text" class="form-input" :placeholder="$t('admin.banReasonPlaceholder')" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('admin.banTypeLabel') }}</label>
            <select v-model="newBan.ban_type" class="form-input">
              <option value="TEMPORARY">{{ $t('blacklist.temporary') }}</option>
              <option value="PERMANENT">{{ $t('blacklist.permanent') }}</option>
            </select>
          </div>
          <div v-if="newBan.ban_type === 'TEMPORARY'" class="form-group">
            <label class="form-label">{{ $t('admin.durationLabel') }}</label>
            <input v-model.number="newBan.duration_minutes" type="number" class="form-input" min="1" />
          </div>
        </div>
        <div class="dialog__footer">
          <button class="btn" @click="addBanDialogVisible = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn--primary" @click="submitBan" :disabled="!newBan.reason">{{ $t('admin.confirmBan') }}</button>
        </div>
      </div>
    </div>
    
    <!-- Extend Ban Dialog -->
    <div v-if="extendDialogVisible" class="dialog-overlay" @click.self="extendDialogVisible = false">
      <div class="dialog">
        <div class="dialog__header">
          <h3>{{ $t('admin.extendBanTitle') }}</h3>
          <button class="dialog__close" @click="extendDialogVisible = false">&times;</button>
        </div>
        <div class="dialog__body">
          <div class="form-group">
            <label class="form-label">{{ $t('admin.extendTime') }}</label>
            <input v-model.number="extendMinutes" type="number" class="form-input" min="1" />
          </div>
        </div>
        <div class="dialog__footer">
          <button class="btn" @click="extendDialogVisible = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn--primary" @click="submitExtend">{{ $t('common.confirm') }}</button>
        </div>
      </div>
    </div>
    
    <!-- Handle Appeal Dialog -->
    <div v-if="appealDialogVisible" class="dialog-overlay" @click.self="appealDialogVisible = false">
      <div class="dialog">
        <div class="dialog__header">
          <h3>{{ appealAction === 'approved' ? $t('admin.approveAppealTitle') : $t('admin.rejectAppealTitle') }}</h3>
          <button class="dialog__close" @click="appealDialogVisible = false">&times;</button>
        </div>
        <div class="dialog__body">
          <div class="form-group">
            <label class="form-label">{{ $t('admin.responseContent') }}</label>
            <textarea v-model="appealResponse" class="form-input form-textarea" rows="3" :placeholder="$t('admin.responseOptional')"></textarea>
          </div>
        </div>
        <div class="dialog__footer">
          <button class="btn" @click="appealDialogVisible = false">{{ $t('common.cancel') }}</button>
          <button class="btn" :class="appealAction === 'approved' ? 'btn--success' : 'btn--danger'" @click="submitAppealHandle">
            {{ appealAction === 'approved' ? $t('admin.confirmApprove') : $t('admin.confirmReject') }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Violation Detail Modal -->
    <div v-if="showingViolation" class="modal-overlay" @click.self="showingViolation = null">
      <div class="modal-content violation-detail-modal">
        <div class="modal-header">
          <h3>{{ $t('admin.violationDetail') }}</h3>
          <button class="modal-close" @click="showingViolation = null">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.violationId') }}:</span>
            <span class="detail-value">{{ showingViolation.id }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.ipAddressLabel') }}:</span>
            <span class="detail-value">{{ showingViolation.ip_address }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.userLabel') }}:</span>
            <span class="detail-value">{{ showingViolation.username || $t('admin.guestUser') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.violationType') }}:</span>
            <span class="detail-value">
              <span class="badge" :class="showingViolation.violation_type === 'audit_failed' ? 'badge--danger' : 'badge--warning'">
                {{ showingViolation.violation_type === 'audit_failed' ? $t('admin.auditFailedType') : $t('admin.rateLimitExceededType') }}
              </span>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.imageIdLabel') }}:</span>
            <span class="detail-value">{{ showingViolation.image_id || '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.violationTime') }}:</span>
            <span class="detail-value">{{ formatDate(showingViolation.created_at) }}</span>
          </div>
          <div class="detail-row detail-row--full">
            <span class="detail-label">{{ $t('admin.detailInfo') }}:</span>
            <pre class="detail-json">{{ formatDetailJson(showingViolation.details) }}</pre>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--secondary" @click="showingViolation = null">{{ $t('admin.closeAction') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useSiteStore } from '@/stores/site'
import { formatDateTime } from '@/utils/timezone'

const { t } = useI18n()
const siteStore = useSiteStore()

const tabs = computed(() => [
  { key: 'settings', label: t('blacklist.securitySettings') },
  { key: 'blacklist', label: t('blacklist.banList') },
  { key: 'violations', label: t('blacklist.violationRecords') },
  { key: 'appeals', label: t('blacklist.appealHandling') },
  { key: 'audit', label: t('admin.auditLogs') },
])

const activeTab = ref('settings')
const pageSize = 20

// Stats
const stats = reactive({
  total_bans: 0,
  active_bans: 0,
  violations_24h: 0,
  pending_appeals: 0,
})

// Security Settings
const securitySettings = reactive({
  rate_limit_guest_per_minute: 3,
  rate_limit_guest_per_hour: 10,
  rate_limit_guest_per_day: 30,
  rate_limit_user_per_minute: 10,
  rate_limit_user_per_hour: 100,
  rate_limit_user_per_day: 500,
  auto_ban_enabled: true,
  audit_fail_threshold: 3,
  rate_exceed_threshold: 3,
  temp_ban_duration: 1440,  // 24 hours in minutes
  rate_limit_login_attempts: 5,
  trust_proxy: true,
  real_ip_header: 'X-Forwarded-For',
})
const savingSettings = ref(false)

// Blacklist
const blacklist = ref([])
const blacklistSearch = ref('')
const activeOnly = ref(false)  // Default to show all
const blacklistPage = ref(1)
const blacklistTotal = ref(0)
const loadingBlacklist = ref(false)

// Violations
const violations = ref([])
const violationTypeFilter = ref('')
const violationsPage = ref(1)
const violationsTotal = ref(0)
const loadingViolations = ref(false)
const showingViolation = ref(null)  // 当前显示详情的违规记录

// Appeals
const appeals = ref([])
const appealStatusFilter = ref('')  // Empty = show all
const appealsPage = ref(1)
const appealsTotal = ref(0)
const loadingAppeals = ref(false)

// Audit Logs
const auditLogs = ref([])
const auditActionFilter = ref('')
const auditResourceFilter = ref('')
const auditPage = ref(1)
const auditTotal = ref(0)
const loadingAudit = ref(false)

// Dialogs
const addBanDialogVisible = ref(false)
const newBan = reactive({
  ip_address: '',
  user_id: null,
  reason: '',
  ban_type: 'TEMPORARY',
  duration_minutes: 1440,
})

const extendDialogVisible = ref(false)
const extendMinutes = ref(60)
const extendingBan = ref(null)

const appealDialogVisible = ref(false)
const appealAction = ref('')
const appealResponse = ref('')
const handlingAppeal = ref(null)

// Load functions
const loadStats = async () => {
  try {
    const res = await api.get('/admin/blacklist/stats')
    Object.assign(stats, res.data)
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

const loadBlacklist = async () => {
  loadingBlacklist.value = true
  try {
    const params = {
      page: blacklistPage.value,
      page_size: pageSize,
    }
    if (blacklistSearch.value) {
      params.search = blacklistSearch.value
    }
    // Only send active_only when true
    if (activeOnly.value) {
      params.active_only = 'true'
    }
    console.log('loadBlacklist params:', params)
    const res = await api.get('/admin/blacklist', { params })
    blacklist.value = res.data.items
    blacklistTotal.value = res.data.total
    console.log('loadBlacklist result:', res.data.total, 'items')
  } catch (e) {
    console.error('loadBlacklist error:', e)
    ElMessage.error(t('error.loadFailed'))
  } finally {
    loadingBlacklist.value = false
  }
}

const loadViolations = async () => {
  loadingViolations.value = true
  try {
    const res = await api.get('/admin/blacklist/violations', {
      params: {
        page: violationsPage.value,
        page_size: pageSize,
        violation_type: violationTypeFilter.value || undefined,
      }
    })
    violations.value = res.data.items
    violationsTotal.value = res.data.total
  } catch (e) {
    ElMessage.error(t('error.loadFailed'))
  } finally {
    loadingViolations.value = false
  }
}

const loadAppeals = async () => {
  loadingAppeals.value = true
  try {
    const params = {
      page: appealsPage.value,
      page_size: pageSize,
    }
    // Only send status_filter when it has a value
    if (appealStatusFilter.value) {
      params.status_filter = appealStatusFilter.value
    }
    console.log('loadAppeals params:', params)
    const res = await api.get('/admin/blacklist/appeals', { params })
    appeals.value = res.data.items
    appealsTotal.value = res.data.total
    console.log('loadAppeals result:', res.data.total, 'items')
  } catch (e) {
    console.error('loadAppeals error:', e)
    ElMessage.error(t('error.loadFailed'))
  } finally {
    loadingAppeals.value = false
  }
}

const loadAuditLogs = async () => {
  loadingAudit.value = true
  try {
    const params = {
      page: auditPage.value,
      page_size: pageSize,
    }
    if (auditActionFilter.value) params.action = auditActionFilter.value
    if (auditResourceFilter.value) params.resource_type = auditResourceFilter.value
    
    const res = await api.get('/admin/audit-logs', { params })
    auditLogs.value = res.data.items
    auditTotal.value = res.data.total
  } catch (e) {
    ElMessage.error(t('error.loadFailed'))
  } finally {
    loadingAudit.value = false
  }
}

const loadSecuritySettings = async () => {
  try {
    const res = await api.get('/admin/settings/security')
    console.log('Loaded security settings response:', res.data)
    const settings = res.data.settings || []
    console.log('Settings array:', settings)
    settings.forEach(s => {
      const keyPart = s.key.replace('security_', '')
      console.log(`Processing: ${s.key} -> ${keyPart} = ${s.value}`)
      if (keyPart in securitySettings) {
        // Handle boolean fields
        if (keyPart === 'auto_ban_enabled' || keyPart === 'trust_proxy') {
          securitySettings[keyPart] = s.value === 'true'
        // Handle string fields
        } else if (keyPart === 'real_ip_header') {
          securitySettings[keyPart] = s.value || 'X-Forwarded-For'
        // Handle numeric fields
        } else {
          securitySettings[keyPart] = parseInt(s.value) || securitySettings[keyPart]
        }
      }
    })
    console.log('Final securitySettings:', JSON.parse(JSON.stringify(securitySettings)))
  } catch (e) {
    console.error('Failed to load security settings:', e)
  }
}

const saveSecuritySettings = async () => {
  savingSettings.value = true
  try {
    const data = {}
    Object.keys(securitySettings).forEach(key => {
      data[`security_${key}`] = String(securitySettings[key])
    })
    const res = await api.post('/admin/settings/batch', data)
    console.log('Save response:', res.data)
    ElMessage.success(t('settings.saveSuccess'))
  } catch (e) {
    console.error('Save failed:', e)
    ElMessage.error(t('error.saveFailed'))
  } finally {
    savingSettings.value = false
  }
}

const switchTab = (key) => {
  activeTab.value = key
  if (key === 'blacklist' && blacklist.value.length === 0) loadBlacklist()
  if (key === 'violations' && violations.value.length === 0) loadViolations()
  if (key === 'appeals' && appeals.value.length === 0) loadAppeals()
  if (key === 'audit' && auditLogs.value.length === 0) loadAuditLogs()
}

// Actions
const showAddBanDialog = () => {
  Object.assign(newBan, {
    ip_address: '',
    user_id: null,
    reason: '',
    ban_type: 'TEMPORARY',
    duration_minutes: 1440,
  })
  addBanDialogVisible.value = true
}

const submitBan = async () => {
  if (!newBan.ip_address && !newBan.user_id) {
    ElMessage.warning(t('error.fieldRequired'))
    return
  }
  try {
    await api.post('/admin/blacklist', newBan)
    ElMessage.success(t('common.success'))
    addBanDialogVisible.value = false
    loadBlacklist()
    loadStats()
  } catch (e) {
    ElMessage.error(t('error.submitFailed'))
  }
}

const removeBan = async (ban) => {
  try {
    await ElMessageBox.confirm(t('blacklist.liftBan'), t('common.confirm'))
    await api.delete(`/admin/blacklist/${ban.id}`)
    ElMessage.success(t('common.success'))
    loadBlacklist()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(t('error.submitFailed'))
  }
}

const extendBan = (ban) => {
  extendingBan.value = ban
  extendMinutes.value = 60
  extendDialogVisible.value = true
}

const submitExtend = async () => {
  try {
    await api.put(`/admin/blacklist/${extendingBan.value.id}/extend`, null, {
      params: { minutes: extendMinutes.value }
    })
    ElMessage.success(t('common.success'))
    extendDialogVisible.value = false
    loadBlacklist()
  } catch (e) {
    ElMessage.error(t('error.submitFailed'))
  }
}

const handleAppeal = (appeal, action) => {
  handlingAppeal.value = appeal
  appealAction.value = action
  appealResponse.value = ''
  appealDialogVisible.value = true
}

const submitAppealHandle = async () => {
  try {
    await api.put(`/admin/blacklist/appeals/${handlingAppeal.value.id}`, {
      status: appealAction.value,
      admin_response: appealResponse.value || null,
    })
    ElMessage.success(t('common.success'))
    appealDialogVisible.value = false
    loadAppeals()
    loadStats()
    if (appealAction.value === 'approved') {
      loadBlacklist()
    }
  } catch (e) {
    ElMessage.error(t('error.submitFailed'))
  }
}

// Helpers
const formatDate = (dateStr) => {
  return formatDateTime(dateStr, siteStore.timezone())
}

const parseDetails = (details) => {
  if (!details) return '-'
  try {
    const obj = JSON.parse(details)
    if (obj.limit_type) {
      if (obj.limit_type === 'minute') return t('admin.minuteLimit')
      if (obj.limit_type === 'hour') return t('admin.hourLimit')
      return t('admin.dailyLimit')
    }
    if (obj.audit_result) return obj.audit_result.substring(0, 50)
    return JSON.stringify(obj).substring(0, 50)
  } catch {
    return details.substring(0, 50)
  }
}

const showViolationDetail = (violation) => {
  showingViolation.value = violation
}

const formatDetailJson = (details) => {
  if (!details) return '-'
  try {
    const obj = JSON.parse(details)
    return JSON.stringify(obj, null, 2)
  } catch {
    return details
  }
}

const getAppealStatusClass = (status) => {
  const s = status?.toUpperCase()
  if (s === 'PENDING') return 'badge--warning'
  if (s === 'APPROVED') return 'badge--success'
  if (s === 'REJECTED') return 'badge--danger'
  return ''
}

const getAppealStatusText = (status) => {
  const s = status?.toUpperCase()
  if (s === 'PENDING') return t('admin.pendingStatus')
  if (s === 'APPROVED') return t('admin.approvedStatus')
  if (s === 'REJECTED') return t('admin.rejectedStatus')
  return status
}

onMounted(() => {
  loadStats()
  loadSecuritySettings()
})
</script>

<style lang="scss" scoped>
.admin-page {
  padding: 24px;
  
  &__title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 24px 0;
  }
}

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  
  &__icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &--danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
    &--warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
    &--info { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
  }
  
  &__value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  &__label {
    font-size: 13px;
    color: var(--text-tertiary);
  }
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 0;
}

.tab {
  padding: 12px 20px;
  background: none;
  border: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
  
  &:hover { color: var(--text-primary); }
  
  &--active {
    color: var(--accent-primary);
    &::after {
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0;
      right: 0;
      height: 2px;
      background: var(--accent-primary);
      border-radius: 1px 1px 0 0;
    }
  }
  
  &__badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 6px;
    background: #ef4444;
    color: white;
    font-size: 11px;
    font-weight: 600;
    border-radius: 9px;
    margin-left: 6px;
  }
}

.settings-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 16px 0;
}

.form-row {
  margin-bottom: 16px;
  
  &--inline {
    display: flex;
    gap: 16px;
  }
  
  &--switch {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  &__label {
    flex: 1;
  }
}

.form-col {
  flex: 1;
  min-width: 0;
}

.form-divider {
  height: 1px;
  background: var(--border-light);
  margin: 24px 0;
}

.form-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-light);
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-suffix {
  font-size: 13px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  
  .label-text {
    display: block;
    color: var(--text-primary);
  }
  
  .label-hint {
    display: block;
    font-size: 12px;
    font-weight: 400;
    color: var(--text-tertiary);
    margin-top: 2px;
  }
}

.form-input {
  width: 100%;
  max-width: 200px;
  padding: 8px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: var(--accent-primary);
  }
  
  &[type="number"] {
    max-width: 100px;
  }
}

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
    }
    
    &:checked + .switch__slider::before {
      transform: translateX(20px);
    }
  }
  
  &__slider {
    position: absolute;
    inset: 0;
    background: var(--bg-tertiary);
    border-radius: 12px;
    cursor: pointer;
    transition: 0.3s;
    
    &::before {
      content: '';
      position: absolute;
      width: 20px;
      height: 20px;
      left: 2px;
      top: 2px;
      background: white;
      border-radius: 50%;
      transition: 0.3s;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
  }
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.search-box {
  position: relative;
  flex: 1;
  max-width: 300px;
  
  svg {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-tertiary);
  }
  
  input {
    width: 100%;
    padding: 10px 12px 10px 38px;
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 14px;
    
    &:focus {
      outline: none;
      border-color: var(--accent-primary);
    }
  }
}

.filter-select {
  padding: 10px 32px 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpolyline points='6,9 12,15 18,9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  
  input { cursor: pointer; }
}

.btn {
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  transition: all 0.2s;
  
  &:hover { opacity: 0.9; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  
  &--primary { background: var(--accent-primary); color: white; }
  &--success { background: #10b981; color: white; }
  &--danger { background: #ef4444; color: white; }
}

.table-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  
  th, td {
    padding: 14px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-light);
  }
  
  th {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-tertiary);
    background: var(--bg-secondary);
  }
  
  td { font-size: 14px; color: var(--text-primary); }
  
  .cell-primary { font-weight: 500; }
  .cell-sub { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
  .cell-muted { color: var(--text-tertiary); }
  .empty-cell { text-align: center; color: var(--text-tertiary); padding: 40px; }
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 12px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  
  &--primary { background: rgba(59,130,246,0.1); color: #3b82f6; }
  &--success { background: rgba(16,185,129,0.1); color: #10b981; }
  &--warning { background: rgba(245,158,11,0.1); color: #f59e0b; }
  &--danger { background: rgba(239,68,68,0.1); color: #ef4444; }
  &--muted { background: var(--bg-tertiary); color: var(--text-tertiary); }
}

.row-lifted {
  opacity: 0.6;
  background: var(--bg-secondary);
}

.action-btns {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  
  &:hover { background: var(--bg-hover); color: var(--text-primary); }
  &--danger:hover { background: rgba(239,68,68,0.1); color: #ef4444; }
  &--success:hover { background: rgba(16,185,129,0.1); color: #10b981; }
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
      border: 1px solid var(--border-light);
      border-radius: var(--radius-md);
      background: var(--bg-primary);
      color: var(--text-primary);
      font-size: 13px;
      cursor: pointer;
      
      &:disabled { opacity: 0.5; cursor: not-allowed; }
      &:not(:disabled):hover { background: var(--bg-tertiary); }
    }
    
    span { font-size: 13px; color: var(--text-secondary); }
  }
}

.loading {
  display: flex;
  justify-content: center;
  padding: 60px;
  
  &__spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-light);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 440px;
  box-shadow: var(--shadow-lg);
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-light);
    
    h3 { font-size: 18px; font-weight: 600; color: var(--text-primary); margin: 0; }
  }
  
  &__close {
    width: 32px;
    height: 32px;
    border: none;
    background: none;
    font-size: 24px;
    color: var(--text-tertiary);
    cursor: pointer;
    
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
  margin-bottom: 16px;
  
  &:last-child { margin-bottom: 0; }
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: var(--accent-primary);
  }
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2'%3E%3Cpolyline points='6,9 12,15 18,9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
  max-width: 300px;
  cursor: pointer;
}

.ip-header-hint {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: var(--radius-md);
  margin-top: 12px;
  
  svg {
    flex-shrink: 0;
    color: #3b82f6;
    margin-top: 2px;
  }
  
  span {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
  }
  
  code {
    background: var(--bg-secondary);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
    font-family: var(--font-mono, monospace);
  }
}

// Modal styles
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
  
  h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 24px;
  color: var(--text-tertiary);
  cursor: pointer;
  
  &:hover {
    color: var(--text-primary);
  }
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(80vh - 140px);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-light);
}

.violation-detail-modal {
  .detail-row {
    display: flex;
    margin-bottom: 12px;
    
    &--full {
      flex-direction: column;
      
      .detail-label {
        margin-bottom: 8px;
      }
    }
  }
  
  .detail-label {
    width: 100px;
    flex-shrink: 0;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  .detail-value {
    font-size: 14px;
    color: var(--text-primary);
  }
  
  .detail-json {
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    padding: 16px;
    font-size: 12px;
    font-family: var(--font-mono, monospace);
    white-space: pre-wrap;
    word-break: break-all;
    overflow-x: auto;
    margin: 0;
    color: var(--text-primary);
  }
}
</style>
