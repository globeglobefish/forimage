<template>
  <div class="admin-layout">
    <aside class="sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
      <div class="sidebar__header">
        <router-link to="/" class="sidebar__logo">
          <template v-if="currentLogo">
            <img :src="currentLogo" :alt="siteStore.siteName()" class="sidebar__logo-img" />
          </template>
          <template v-else>
            <div class="sidebar__logo-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21,15 16,10 5,21"/>
              </svg>
            </div>
            <span class="sidebar__logo-text" v-if="!sidebarCollapsed">{{ siteStore.siteName() }}</span>
          </template>
        </router-link>
        <span class="sidebar__badge" v-if="!sidebarCollapsed">{{ $t('admin.panel') }}</span>
      </div>
      
      <nav class="sidebar__nav">
        <router-link 
          v-for="item in navItems" 
          :key="item.path"
          :to="item.path" 
          class="sidebar__link" 
          :class="{ 'is-active': isActiveRoute(item.path) }"
          :title="sidebarCollapsed ? item.label : ''"
        >
          <span class="sidebar__link-icon" v-html="item.icon"></span>
          <span class="sidebar__link-text" v-if="!sidebarCollapsed">{{ item.label }}</span>
        </router-link>
      </nav>
      
      <div class="sidebar__footer">
        <button class="sidebar__collapse-btn" @click="toggleSidebar" :title="sidebarCollapsed ? $t('admin.expandSidebar') : $t('admin.collapseSidebar')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline :points="sidebarCollapsed ? '9,18 15,12 9,6' : '15,18 9,12 15,6'"/>
          </svg>
        </button>
        <router-link to="/" class="sidebar__back" v-if="!sidebarCollapsed">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12,19 5,12 12,5"/>
          </svg>
          {{ $t('admin.backToFrontend') }}
        </router-link>
      </div>
    </aside>
    
    <div class="main-area">
      <header class="topbar">
        <div class="topbar__left">
          <button class="topbar__menu-btn" @click="toggleSidebar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <div class="topbar__breadcrumb">
            <span>{{ $t('admin.panel') }}</span>
            <template v-if="currentPageTitle">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9,18 15,12 9,6"/>
              </svg>
              <span>{{ currentPageTitle }}</span>
            </template>
          </div>
        </div>
        
        <div class="topbar__right">
          <ThemeToggle />
          <LanguageSwitcher />
          <div class="user-badge" @click="showUserMenu = !showUserMenu" ref="userMenuRef">
            <div class="user-badge__avatar">{{ userStore.user?.username?.[0]?.toUpperCase() }}</div>
            <span class="user-badge__name">{{ userStore.user?.username }}</span>
            <svg class="user-badge__arrow" :class="{ 'is-open': showUserMenu }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6,9 12,15 18,9"/>
            </svg>
            
            <transition name="dropdown">
              <div v-if="showUserMenu" class="user-dropdown" @click.stop>
                <router-link to="/profile" class="user-dropdown__item" @click="showUserMenu = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                  </svg>
                  {{ $t('nav.profile') }}
                </router-link>
                <div class="user-dropdown__divider"></div>
                <button class="user-dropdown__item user-dropdown__item--danger" @click="handleLogout">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16,17 21,12 16,7"/><line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  {{ $t('auth.logout') }}
                </button>
              </div>
            </transition>
          </div>
        </div>
      </header>
      
      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'
import { useThemeStore } from '@/stores/theme'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import ThemeToggle from '@/components/ThemeToggle.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const siteStore = useSiteStore()
const themeStore = useThemeStore()
const { t } = useI18n()

// Sidebar state
const sidebarCollapsed = ref(localStorage.getItem('admin_sidebar_collapsed') === 'true')
const showUserMenu = ref(false)
const userMenuRef = ref(null)

// Logo based on theme
const currentLogo = computed(() => {
  if (themeStore.isDark && siteStore.siteLogoDark()) {
    return siteStore.siteLogoDark()
  }
  return siteStore.siteLogo()
})

// Navigation items
const navItems = computed(() => [
  {
    path: '/admin',
    label: t('admin.dashboard'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>'
  },
  {
    path: '/admin/users',
    label: t('admin.usersManagement'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
  },
  {
    path: '/admin/images',
    label: t('admin.imagesManagement'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21,15 16,10 5,21"/></svg>'
  },
  {
    path: '/admin/gallery',
    label: t('adminGallery.title'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'
  },
  {
    path: '/admin/settings',
    label: t('admin.systemSettings'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>'
  },
  {
    path: '/admin/blacklist',
    label: t('admin.securityManagement'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/></svg>'
  },
  {
    path: '/admin/backup',
    label: t('backup.title'),
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>'
  }
])

const pageTitles = computed(() => ({
  '/admin': '',
  '/admin/users': t('admin.usersManagement'),
  '/admin/images': t('admin.imagesManagement'),
  '/admin/settings': t('admin.systemSettings'),
  '/admin/blacklist': t('admin.securityManagement'),
  '/admin/backup': t('backup.title'),
  '/admin/gallery': t('adminGallery.title'),
}))

const currentPageTitle = computed(() => pageTitles.value[route.path] || '')

const isActiveRoute = (path) => {
  if (path === '/admin') {
    return route.path === '/admin'
  }
  return route.path.startsWith(path)
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('admin_sidebar_collapsed', sidebarCollapsed.value)
}

const handleLogout = async () => {
  showUserMenu.value = false
  await userStore.logout()
  ElMessage.success(t('admin.logoutSuccess'))
  router.push('/')
}

// Close user menu when clicking outside
const handleClickOutside = (event) => {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>


<style lang="scss" scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-primary);
}

// Sidebar
.sidebar {
  width: 240px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.25s ease;
  
  &.is-collapsed {
    width: 72px;
    
    .sidebar__header {
      padding: 20px 12px;
    }
    
    .sidebar__logo {
      justify-content: center;
    }
    
    .sidebar__logo-img {
      max-width: 40px;
    }
    
    .sidebar__badge {
      display: none;
    }
    
    .sidebar__nav {
      padding: 16px 8px;
    }
    
    .sidebar__link {
      justify-content: center;
      padding: 12px;
    }
    
    .sidebar__footer {
      padding: 12px 8px;
      flex-direction: column;
      gap: 8px;
    }
    
    .sidebar__collapse-btn {
      width: 100%;
    }
  }
  
  &__header {
    padding: 20px;
    border-bottom: 1px solid var(--border-light);
    text-align: center;
    transition: padding 0.25s ease;
  }
  
  &__logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    text-decoration: none;
    transition: all 0.2s ease;
  }
  
  &__logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-radius: var(--radius-md);
    flex-shrink: 0;
  }
  
  &__logo-img {
    height: 32px;
    width: auto;
    max-width: 140px;
    object-fit: contain;
    transition: all 0.2s ease;
  }
  
  &__logo-text {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
  }
  
  &__badge {
    display: block;
    font-size: 10px;
    color: var(--text-tertiary);
    margin-top: 8px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
  }
  
  &__nav {
    flex: 1;
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    overflow-y: auto;
    transition: padding 0.25s ease;
  }
  
  &__link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 14px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition: all 0.15s ease;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-secondary);
    }
    
    &.is-active {
      color: var(--accent-primary);
      background: rgba(var(--accent-primary-rgb), 0.08);
      
      .sidebar__link-icon {
        color: var(--accent-primary);
      }
    }
  }
  
  &__link-icon {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    
    :deep(svg) {
      width: 18px;
      height: 18px;
    }
  }
  
  &__link-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  &__footer {
    padding: 12px;
    border-top: 1px solid var(--border-light);
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.25s ease;
  }
  
  &__collapse-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    color: var(--text-tertiary);
    cursor: pointer;
    transition: all 0.15s ease;
    flex-shrink: 0;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-tertiary);
      border-color: var(--border-medium);
    }
  }
  
  &__back {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: var(--text-tertiary);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition: all 0.15s ease;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-secondary);
    }
  }
}

// Main Area
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

// Topbar
.topbar {
  height: 64px;
  padding: 0 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  
  &__left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  &__menu-btn {
    display: none;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-tertiary);
    }
    
    @media (max-width: 768px) {
      display: flex;
    }
  }
  
  &__breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: var(--text-secondary);
    
    svg { color: var(--text-tertiary); }
  }
  
  &__right {
    display: flex;
    align-items: center;
    gap: 6px;
    height: 36px;
  }
}

// User Badge & Dropdown
.user-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px 3px 3px;
  height: 36px;
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.15s ease;
  
  &:hover { background: var(--bg-tertiary); }
  
  &__avatar {
    width: 30px;
    height: 30px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover));
    color: var(--text-inverse);
    font-size: 12px;
    font-weight: 600;
    border-radius: 50%;
    flex-shrink: 0;
  }
  
  &__name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    
    @media (max-width: 640px) {
      display: none;
    }
  }
  
  &__arrow {
    transition: transform 0.2s ease;
    color: var(--text-tertiary);
    
    &.is-open {
      transform: rotate(180deg);
    }
    
    @media (max-width: 640px) {
      display: none;
    }
  }
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: 6px;
  z-index: 100;
  
  &__item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;
    color: var(--text-secondary);
    text-decoration: none;
    background: none;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s ease;
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-secondary);
    }
    
    &--danger {
      color: #ef4444;
      
      &:hover {
        background: rgba(239, 68, 68, 0.08);
      }
    }
  }
  
  &__divider {
    height: 1px;
    background: var(--border-light);
    margin: 6px 0;
  }
}

// Content
.content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}

// Transitions
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// Responsive
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    
    &.is-collapsed {
      transform: translateX(-100%);
    }
  }
  
  .main-area {
    width: 100%;
  }
  
  .content {
    padding: 16px;
  }
}
</style>
