<template>
  <div class="search-filter">
    <div class="filter-toggle" @click="expanded = !expanded">
      <span class="filter-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
        </svg>
      </span>
      <span>{{ $t('search.title') }}</span>
      <span v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</span>
      <span class="expand-icon" :class="{ 'is-expanded': expanded }">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </span>
    </div>

    <transition name="slide">
      <div v-show="expanded" class="filter-panel">
        <!-- Date Range -->
        <div class="filter-section">
          <label class="filter-label">{{ $t('search.dateRange') }}</label>
          <div class="filter-row">
            <el-date-picker
              v-model="filters.dateFrom"
              type="date"
              :placeholder="$t('search.dateFrom')"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              size="small"
              style="width: 140px"
            />
            <span class="filter-separator">-</span>
            <el-date-picker
              v-model="filters.dateTo"
              type="date"
              :placeholder="$t('search.dateTo')"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              size="small"
              style="width: 140px"
            />
          </div>
        </div>

        <!-- Dimensions -->
        <div class="filter-section">
          <label class="filter-label">{{ $t('search.dimensions') }}</label>
          <div class="filter-grid">
            <div class="filter-input-group">
              <span class="input-label">{{ $t('search.minWidth') }}</span>
              <el-input-number v-model="filters.minWidth" :min="0" :step="100" size="small" controls-position="right" />
            </div>
            <div class="filter-input-group">
              <span class="input-label">{{ $t('search.maxWidth') }}</span>
              <el-input-number v-model="filters.maxWidth" :min="0" :step="100" size="small" controls-position="right" />
            </div>
            <div class="filter-input-group">
              <span class="input-label">{{ $t('search.minHeight') }}</span>
              <el-input-number v-model="filters.minHeight" :min="0" :step="100" size="small" controls-position="right" />
            </div>
            <div class="filter-input-group">
              <span class="input-label">{{ $t('search.maxHeight') }}</span>
              <el-input-number v-model="filters.maxHeight" :min="0" :step="100" size="small" controls-position="right" />
            </div>
          </div>
        </div>

        <!-- Presets -->
        <div class="filter-section">
          <label class="filter-label">{{ $t('search.presets') }}</label>
          <div class="preset-buttons">
            <button class="preset-btn" @click="applyPreset('hd')">{{ $t('search.presetHD') }}</button>
            <button class="preset-btn" @click="applyPreset('fullhd')">{{ $t('search.presetFullHD') }}</button>
            <button class="preset-btn" @click="applyPreset('4k')">{{ $t('search.preset4K') }}</button>
          </div>
        </div>

        <!-- Actions -->
        <div class="filter-actions">
          <button class="btn btn--secondary btn--sm" @click="resetFilters">{{ $t('search.resetFilters') }}</button>
          <button class="btn btn--primary btn--sm" @click="applyFilters">{{ $t('search.applyFilters') }}</button>
        </div>
      </div>
    </transition>

    <!-- Active Filters Display -->
    <div v-if="activeFilterCount > 0" class="active-filters">
      <span class="active-label">{{ $t('search.activeFilters') }}:</span>
      <span v-if="filters.dateFrom || filters.dateTo" class="filter-tag">
        {{ formatDateRange }}
        <button class="tag-close" @click="clearDateFilter">×</button>
      </span>
      <span v-if="hasDimensionFilter" class="filter-tag">
        {{ formatDimensions }}
        <button class="tag-close" @click="clearDimensionFilter">×</button>
      </span>
      <button class="clear-all" @click="resetFilters">{{ $t('search.clearFilters') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits(['filter-change'])

const expanded = ref(false)
const filters = ref({
  dateFrom: null,
  dateTo: null,
  minWidth: null,
  maxWidth: null,
  minHeight: null,
  maxHeight: null,
})

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.dateFrom || filters.value.dateTo) count++
  if (filters.value.minWidth || filters.value.maxWidth || filters.value.minHeight || filters.value.maxHeight) count++
  return count
})

const hasDimensionFilter = computed(() => {
  return filters.value.minWidth || filters.value.maxWidth || filters.value.minHeight || filters.value.maxHeight
})

const formatDateRange = computed(() => {
  const from = filters.value.dateFrom || '...'
  const to = filters.value.dateTo || '...'
  return `${from} ~ ${to}`
})

const formatDimensions = computed(() => {
  const parts = []
  if (filters.value.minWidth) parts.push(`W≥${filters.value.minWidth}`)
  if (filters.value.maxWidth) parts.push(`W≤${filters.value.maxWidth}`)
  if (filters.value.minHeight) parts.push(`H≥${filters.value.minHeight}`)
  if (filters.value.maxHeight) parts.push(`H≤${filters.value.maxHeight}`)
  return parts.join(', ')
})

const applyPreset = (preset) => {
  switch (preset) {
    case 'hd':
      filters.value.minWidth = 1280
      filters.value.minHeight = 720
      break
    case 'fullhd':
      filters.value.minWidth = 1920
      filters.value.minHeight = 1080
      break
    case '4k':
      filters.value.minWidth = 3840
      filters.value.minHeight = 2160
      break
  }
}

const clearDateFilter = () => {
  filters.value.dateFrom = null
  filters.value.dateTo = null
  applyFilters()
}

const clearDimensionFilter = () => {
  filters.value.minWidth = null
  filters.value.maxWidth = null
  filters.value.minHeight = null
  filters.value.maxHeight = null
  applyFilters()
}

const resetFilters = () => {
  filters.value = {
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
  emit('filter-change', { ...filters.value })
}
</script>

<style lang="scss" scoped>
.search-filter {
  position: relative;
}

.filter-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.15s;
  white-space: nowrap;

  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
}

.filter-icon {
  display: flex;
  opacity: 0.7;
}

.filter-badge {
  background: var(--accent-primary);
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.expand-icon {
  display: flex;
  transition: transform 0.2s;
  
  &.is-expanded {
    transform: rotate(180deg);
  }
}

.filter-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 100;
  min-width: 360px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.filter-section {
  margin-bottom: 16px;
  
  &:last-of-type {
    margin-bottom: 20px;
  }
}

.filter-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-separator {
  color: var(--text-tertiary);
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.filter-input-group {
  .input-label {
    display: block;
    font-size: 12px;
    color: var(--text-tertiary);
    margin-bottom: 4px;
  }
  
  .el-input-number {
    width: 100%;
  }
}

.preset-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-btn {
  padding: 6px 12px;
  font-size: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
    color: var(--text-primary);
  }
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.active-filters {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  font-size: 13px;
  white-space: nowrap;
}

.active-label {
  color: var(--text-tertiary);
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
}

.tag-close {
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

.clear-all {
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

// Transition
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// Button styles
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--primary {
    background: var(--accent-primary);
    color: white;
    
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
  
  &--sm {
    padding: 6px 12px;
    font-size: 12px;
  }
}
</style>
