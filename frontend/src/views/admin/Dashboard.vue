<template>
  <div class="dashboard">
    <h2 class="dashboard__title">{{ $t('admin.dashboard') }}</h2>
    
    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-card__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ stats.total_users }}</div>
          <div class="stat-card__label">{{ $t('admin.totalUsers') }}</div>
        </div>
        <div class="stat-card__extra">{{ $t('admin.today') }} +{{ stats.today_registrations }}</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-card__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21,15 16,10 5,21"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ stats.total_images }}</div>
          <div class="stat-card__label">{{ $t('admin.totalImages') }}</div>
        </div>
        <div class="stat-card__extra">{{ $t('admin.today') }} +{{ stats.today_uploads }}</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-card__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ formatSize(stats.total_storage_bytes) }}</div>
          <div class="stat-card__label">{{ $t('admin.storageUsed') }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-card__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>
          </svg>
        </div>
        <div class="stat-card__content">
          <div class="stat-card__value">{{ stats.pending_images }}</div>
          <div class="stat-card__label">{{ $t('admin.pendingReview') }}</div>
        </div>
      </div>
    </div>
    
    <div class="chart-card">
      <h3 class="chart-card__title">{{ $t('admin.last30Days') }}</h3>
      <div class="chart-card__container" ref="chartRef"></div>
    </div>
    
    <div class="info-grid">
      <div class="info-card">
        <h3 class="info-card__title">{{ $t('admin.userStatus') }}</h3>
        <div class="info-card__list" v-if="stats">
          <div class="info-card__item">
            <span class="info-card__label">{{ $t('admin.activeUsers') }}</span>
            <span class="info-card__value info-card__value--success">{{ stats.active_users }}</span>
          </div>
          <div class="info-card__item">
            <span class="info-card__label">{{ $t('admin.pendingUsers') }}</span>
            <span class="info-card__value info-card__value--warning">{{ stats.pending_users }}</span>
          </div>
          <div class="info-card__item">
            <span class="info-card__label">{{ $t('admin.disabledUsers') }}</span>
            <span class="info-card__value info-card__value--danger">{{ stats.disabled_users }}</span>
          </div>
        </div>
      </div>
      
      <div class="info-card">
        <h3 class="info-card__title">{{ $t('admin.imageStatus') }}</h3>
        <div class="info-card__list" v-if="stats">
          <div class="info-card__item">
            <span class="info-card__label">{{ $t('common.approved') }}</span>
            <span class="info-card__value info-card__value--success">{{ stats.approved_images }}</span>
          </div>
          <div class="info-card__item">
            <span class="info-card__label">{{ $t('common.pending') }}</span>
            <span class="info-card__value info-card__value--warning">{{ stats.pending_images }}</span>
          </div>
          <div class="info-card__item">
            <span class="info-card__label">{{ $t('common.rejected') }}</span>
            <span class="info-card__value info-card__value--danger">{{ stats.rejected_images }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n()
const stats = ref(null)
const dailyStats = ref([])
const chartRef = ref(null)
let chart = null

const loadDashboard = async () => {
  try {
    const response = await api.get('/admin/dashboard')
    stats.value = response.data.stats
    dailyStats.value = response.data.daily_stats
    renderChart()
  } catch (error) {
    console.error(error)
  }
}

const renderChart = () => {
  if (!chartRef.value || !dailyStats.value.length) return
  
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const textColor = isDark ? '#a8a29e' : '#78716c'
  const lineColor = isDark ? '#292524' : '#e7e5e4'
  
  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: [t('admin.uploads'), t('admin.registrations')],
      textStyle: { color: textColor },
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dailyStats.value.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: lineColor } },
      axisLabel: { color: textColor },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: lineColor } },
      axisLabel: { color: textColor },
    },
    series: [
      {
        name: t('admin.uploads'),
        type: 'line',
        smooth: true,
        data: dailyStats.value.map(d => d.uploads),
        itemStyle: { color: '#78716c' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(120, 113, 108, 0.2)' },
            { offset: 1, color: 'rgba(120, 113, 108, 0)' },
          ]),
        },
      },
      {
        name: t('admin.registrations'),
        type: 'line',
        smooth: true,
        data: dailyStats.value.map(d => d.registrations),
        itemStyle: { color: '#a8a29e' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(168, 162, 158, 0.2)' },
            { offset: 1, color: 'rgba(168, 162, 158, 0)' },
          ]),
        },
      },
    ],
  }
  
  chart.setOption(option)
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB'
  return (bytes / 1073741824).toFixed(2) + ' GB'
}

const handleResize = () => chart?.resize()

onMounted(() => {
  loadDashboard()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard {
  &__title {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 24px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-neu-flat);
  position: relative;
  
  &__icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
  }
  
  &__content {
    flex: 1;
  }
  
  &__value {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  &__label {
    font-size: 13px;
    color: var(--text-tertiary);
    margin-top: 2px;
  }
  
  &__extra {
    position: absolute;
    right: 16px;
    bottom: 12px;
    font-size: 11px;
    color: var(--text-tertiary);
  }
}

.chart-card {
  padding: 24px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-neu-flat);
  margin-bottom: 24px;
  
  &__title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 20px;
  }
  
  &__container {
    height: 280px;
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-card {
  padding: 24px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-neu-flat);
  
  &__title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 16px;
  }
  
  &__list {
    display: flex;
    flex-direction: column;
  }
  
  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-light);
    
    &:last-child { border-bottom: none; }
  }
  
  &__label {
    font-size: 14px;
    color: var(--text-secondary);
  }
  
  &__value {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    
    &--success { color: var(--accent-success); }
    &--warning { color: var(--accent-warning); }
    &--danger { color: var(--accent-danger); }
  }
}

@media (max-width: 1000px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
