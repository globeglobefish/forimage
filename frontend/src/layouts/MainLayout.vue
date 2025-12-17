<template>
  <div class="layout">
    <!-- Header -->
    <header class="header">
      <div class="header__container">
        <!-- Left: Logo -->
        <router-link to="/" class="logo">
          <div class="logo__wrapper">
            <template v-if="currentLogo">
              <img :src="currentLogo" :alt="siteStore.siteName()" class="logo__image" />
            </template>
            <template v-else>
              <div class="logo__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21,15 16,10 5,21"/>
                </svg>
              </div>
              <span class="logo__text">{{ siteStore.siteName() }}</span>
            </template>
          </div>
        </router-link>
        
        <!-- Center: Desktop Navigation -->
        <nav class="nav nav--desktop">
          <router-link to="/" class="nav__link" exact-active-class="nav__link--active">
            {{ $t('nav.home') }}
          </router-link>
          <router-link to="/gallery" class="nav__link" :class="{ 'nav__link--active': isGalleryActive }">
            {{ $t('nav.gallery') }}
          </router-link>
          <template v-if="userStore.isLoggedIn">
            <router-link to="/my-images" class="nav__link" :class="{ 'nav__link--active': isMyImagesActive }">
              {{ $t('nav.myImages') }}
            </router-link>
            <router-link to="/albums" class="nav__link" :class="{ 'nav__link--active': isAlbumsActive }">
              {{ $t('nav.albums') }}
            </router-link>
          </template>
        </nav>
        
        <!-- Right: Controls -->
        <div class="header__right">
          <!-- Desktop Controls -->
          <div class="header__controls desktop-only">
            <ThemeToggle />
            <LanguageSwitcher />
          </div>
          
          <!-- Desktop User Menu (hidden on mobile) -->
          <template v-if="userStore.isLoggedIn">
            <!-- Ban Status Badge -->
            <div v-if="isBanned" class="ban-badge desktop-only" @click="showAppealDialog">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
              </svg>
              <span>{{ $t('blacklist.banned') }}</span>
            </div>
            
            <div class="user-dropdown desktop-only" ref="userDropdownRef">
              <button class="user-menu" @click="userMenuOpen = !userMenuOpen">
                <div class="user-menu__avatar" :class="{ 'user-menu__avatar--banned': isBanned }">
                  {{ userStore.user?.username?.[0]?.toUpperCase() }}
                </div>
                <span class="user-menu__name">{{ userStore.user?.username }}</span>
                <svg class="user-menu__arrow" :class="{ 'is-open': userMenuOpen }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6,9 12,15 18,9"/>
                </svg>
              </button>
              <transition name="dropdown">
                <div v-if="userMenuOpen" class="user-dropdown__menu">
                  <button class="user-dropdown__item" @click="handleUserCommand('profile')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                    <span>{{ $t('nav.profile') }}</span>
                  </button>
                  <button v-if="isBanned" class="user-dropdown__item user-dropdown__item--warn" @click="handleUserCommand('ban-status')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
                    </svg>
                    <span>{{ $t('appeal.title') }}</span>
                  </button>
                  <button v-if="userStore.isAdmin" class="user-dropdown__item" @click="handleUserCommand('admin')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                    <span>{{ $t('nav.admin') }}</span>
                  </button>
                  <div class="user-dropdown__divider"></div>
                  <button class="user-dropdown__item user-dropdown__item--danger" @click="handleUserCommand('logout')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                      <polyline points="16,17 21,12 16,7"/>
                      <line x1="21" y1="12" x2="9" y2="12"/>
                    </svg>
                    <span>{{ $t('auth.logout') }}</span>
                  </button>
                </div>
              </transition>
            </div>
          </template>
          
          <!-- Guest buttons (Desktop) - Capsule Design -->
          <template v-if="!userStore.isLoggedIn">
            <div class="auth-capsule desktop-only">
              <router-link to="/login" class="auth-capsule__btn auth-capsule__btn--login">{{ $t('auth.login') }}</router-link>
              <router-link to="/register" class="auth-capsule__btn auth-capsule__btn--register">{{ $t('auth.register') }}</router-link>
            </div>
          </template>
          
          <!-- Mobile Menu Toggle (Always visible on mobile) -->
          <button 
            class="mobile-menu-toggle"
            @click="mobileMenuOpen = !mobileMenuOpen"
            :class="{ 'is-active': mobileMenuOpen }"
          >
            <span class="hamburger"></span>
          </button>
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Mobile Navigation Drawer (Available for ALL users) -->
    <transition name="slide">
      <div v-if="mobileMenuOpen" class="mobile-nav-overlay" @click="mobileMenuOpen = false">
        <nav class="mobile-nav" @click.stop>
          <div class="mobile-nav__links">
            <!-- Public Navigation Links (for all users) -->
            <div class="mobile-nav__section-title">{{ $t('nav.navigation') || '导航' }}</div>
            <router-link to="/" class="mobile-nav__link" exact-active-class="mobile-nav__link--active" @click="mobileMenuOpen = false">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9,22 9,12 15,12 15,22"/>
              </svg>
              {{ $t('nav.home') }}
            </router-link>
            <router-link to="/gallery" class="mobile-nav__link" :class="{ 'mobile-nav__link--active': isGalleryActive }" @click="mobileMenuOpen = false">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
              </svg>
              {{ $t('nav.gallery') }}
            </router-link>
            
            <!-- User-only Navigation Links -->
            <template v-if="userStore.isLoggedIn">
              <router-link to="/my-images" class="mobile-nav__link" :class="{ 'mobile-nav__link--active': isMyImagesActive }" @click="mobileMenuOpen = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21,15 16,10 5,21"/>
                </svg>
                {{ $t('nav.myImages') }}
              </router-link>
              <router-link to="/albums" class="mobile-nav__link" :class="{ 'mobile-nav__link--active': isAlbumsActive }" @click="mobileMenuOpen = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                {{ $t('nav.albums') }}
              </router-link>
              
              <div class="mobile-nav__divider"></div>
              
              <div class="mobile-nav__section-title">{{ $t('nav.account') || '账户' }}</div>
              <router-link to="/profile" class="mobile-nav__link" @click="mobileMenuOpen = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                {{ $t('nav.profile') }}
              </router-link>
              <router-link v-if="userStore.isAdmin" to="/admin" class="mobile-nav__link" @click="mobileMenuOpen = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
                {{ $t('nav.admin') }}
              </router-link>
              <button class="mobile-nav__link mobile-nav__link--danger" @click="handleMobileLogout">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                  <polyline points="16,17 21,12 16,7"/>
                  <line x1="21" y1="12" x2="9" y2="12"/>
                </svg>
                {{ $t('auth.logout') }}
              </button>
            </template>
            
            <!-- Guest Auth Links -->
            <template v-else>
              <div class="mobile-nav__divider"></div>
              <div class="mobile-nav__section-title">{{ $t('auth.account') }}</div>
              <router-link to="/login" class="mobile-nav__link" @click="mobileMenuOpen = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                  <polyline points="10,17 15,12 10,7"/>
                  <line x1="15" y1="12" x2="3" y2="12"/>
                </svg>
                {{ $t('auth.login') }}
              </router-link>
              <router-link to="/register" class="mobile-nav__link mobile-nav__link--primary" @click="mobileMenuOpen = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="8.5" cy="7" r="4"/>
                  <line x1="20" y1="8" x2="20" y2="14"/>
                  <line x1="23" y1="11" x2="17" y2="11"/>
                </svg>
                {{ $t('auth.register') }}
              </router-link>
            </template>
            
            <div class="mobile-nav__divider"></div>
            
            <!-- Settings Section (Available for ALL users) -->
            <div class="mobile-nav__section-title">{{ $t('settings.general') }}</div>
            
            <!-- Language Selection -->
            <div class="mobile-nav__setting-group">
              <span class="mobile-nav__setting-label">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                {{ $t('language.language') }}
              </span>
              <div class="mobile-lang-switcher">
                <button 
                  v-for="locale in locales" 
                  :key="locale.code"
                  @click="handleMobileLanguageSwitch(locale.code)"
                  class="mobile-lang-btn"
                  :class="{ 'is-active': locale.code === currentLocale }"
                >
                  <span class="mobile-lang-btn__name">{{ locale.name }}</span>
                  <svg v-if="locale.code === currentLocale" class="mobile-lang-btn__check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20,6 9,17 4,12"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <!-- Theme Toggle -->
            <div class="mobile-nav__setting-group">
              <span class="mobile-nav__setting-label">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="5"/>
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                </svg>
                {{ $t('theme.theme') }}
              </span>
              <button @click="handleMobileThemeToggle" class="mobile-theme-btn">
                <svg v-if="themeStore.isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="5"/>
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                </svg>
                <span>{{ themeStore.isDark ? $t('theme.light') : $t('theme.dark') }}</span>
              </button>
            </div>
          </div>
          
          <!-- User Info (for logged in users) -->
          <div class="mobile-nav__user" v-if="userStore.isLoggedIn && userStore.user">
            <div class="mobile-nav__avatar" :class="{ 'mobile-nav__avatar--banned': isBanned }">
              {{ userStore.user?.username?.[0]?.toUpperCase() }}
            </div>
            <div class="mobile-nav__user-info">
              <span class="mobile-nav__username">{{ userStore.user?.username }}</span>
              <span v-if="isBanned" class="mobile-nav__ban-tag">{{ $t('blacklist.banned') }}</span>
            </div>
          </div>
        </nav>
      </div>
    </transition>
    
    <!-- Footer -->
    <footer class="footer">
      <div class="footer__container">
        <p class="footer__text">
          &copy; {{ new Date().getFullYear() }} {{ siteStore.siteFooter() }}
        </p>
      </div>
    </footer>
    
    <!-- Ban Appeal Dialog -->
    <div v-if="appealDialogVisible" class="dialog-overlay" @click.self="appealDialogVisible = false">
      <div class="dialog appeal-dialog">
        <div class="dialog__header">
          <h3 class="dialog__title">{{ $t('appeal.title') }}</h3>
          <button class="dialog__close" @click="appealDialogVisible = false">&times;</button>
        </div>
        <div class="dialog__body">
          <div class="ban-info">
            <div class="ban-info__item">
              <span class="ban-info__label">{{ $t('blacklist.status') }}</span>
              <span class="ban-info__value ban-info__value--danger">{{ $t('blacklist.banned') }}</span>
            </div>
            <div class="ban-info__item">
              <span class="ban-info__label">{{ $t('blacklist.reason') }}</span>
              <span class="ban-info__value">{{ banStatus?.reason || $t('common.unknown') }}</span>
            </div>
          </div>
          
          <div v-if="!hasPendingAppeal && banStatus?.appeal_status !== 'APPROVED'" class="appeal-form">
            <div class="form-divider"></div>
            <h4 class="appeal-form__title">{{ $t('appeal.submit') }}</h4>
            <textarea 
              v-model="appealReason" 
              class="form-textarea" 
              :placeholder="$t('appeal.reasonPlaceholder')"
              rows="4"
            ></textarea>
          </div>
        </div>
        <div class="dialog__footer">
          <button class="btn btn--secondary" @click="appealDialogVisible = false">{{ $t('common.close') }}</button>
          <button 
            v-if="!hasPendingAppeal && banStatus?.appeal_status !== 'APPROVED'" 
            class="btn btn--primary" 
            @click="submitAppeal"
            :disabled="submittingAppeal"
          >
            {{ submittingAppeal ? $t('common.submitting') : $t('common.submit') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


<script setup>
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { useSiteStore } from '@/stores/site'
import { useLocaleStore } from '@/stores/locale'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ThemeToggle from '@/components/ThemeToggle.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { useI18n } from 'vue-i18n'
import { onMounted, onUnmounted, ref, computed } from 'vue'
import api from '@/api'

const userStore = useUserStore()
const themeStore = useThemeStore()
const siteStore = useSiteStore()
const localeStore = useLocaleStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()

// Computed properties for navigation active state
const isAlbumsActive = computed(() => route.path.startsWith('/albums'))
const isGalleryActive = computed(() => route.path.startsWith('/gallery'))
const isMyImagesActive = computed(() => route.path.startsWith('/my-images'))

// Language list (hardcoded to ensure availability)
const locales = [
  { code: 'zh-CN', name: '简体中文' },
  { code: 'zh-TW', name: '繁體中文' },
  { code: 'en', name: 'English' },
]

const currentLocale = computed(() => localeStore.currentLocale)

// Mobile menu
const mobileMenuOpen = ref(false)

// User dropdown menu
const userMenuOpen = ref(false)
const userDropdownRef = ref(null)

// Close menus on route change
router.afterEach(() => {
  mobileMenuOpen.value = false
  userMenuOpen.value = false
})

// Close user dropdown when clicking outside
const handleClickOutsideUserMenu = (event) => {
  if (userDropdownRef.value && !userDropdownRef.value.contains(event.target)) {
    userMenuOpen.value = false
  }
}

// Ban status
const banStatus = ref(null)
const appealDialogVisible = ref(false)
const appealReason = ref('')
const submittingAppeal = ref(false)

const isBanned = computed(() => banStatus.value?.is_banned)
const hasPendingAppeal = computed(() => banStatus.value?.appeal_status === 'PENDING')

// Logo based on theme - use dark logo if available in dark mode
const currentLogo = computed(() => {
  if (themeStore.isDark && siteStore.siteLogoDark()) {
    return siteStore.siteLogoDark()
  }
  return siteStore.siteLogo()
})

const checkBanStatus = async () => {
  if (!userStore.isLoggedIn) return
  try {
    const res = await api.get('/appeal/status')
    banStatus.value = res.data
  } catch (e) {
    // Ignore errors
  }
}

const showAppealDialog = () => {
  appealReason.value = ''
  appealDialogVisible.value = true
}

const submitAppeal = async () => {
  if (!appealReason.value.trim()) {
    ElMessage.warning(t('appeal.reasonRequired'))
    return
  }
  submittingAppeal.value = true
  try {
    await api.post('/appeal', { reason: appealReason.value })
    ElMessage.success(t('appeal.submitSuccess'))
    appealDialogVisible.value = false
    await checkBanStatus()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || t('error.submitFailed'))
  } finally {
    submittingAppeal.value = false
  }
}

onMounted(() => {
  themeStore.initTheme()
  localeStore.initLocale()
  checkBanStatus()
  document.addEventListener('click', handleClickOutsideUserMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutsideUserMenu)
})

const handleUserCommand = async (command) => {
  userMenuOpen.value = false
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'admin':
      router.push('/admin')
      break
    case 'ban-status':
      showAppealDialog()
      break
    case 'logout':
      await userStore.logout()
      banStatus.value = null
      ElMessage.success(t('auth.logoutSuccess'))
      router.push('/')
      break
  }
}

const handleMobileLogout = async () => {
  mobileMenuOpen.value = false
  await userStore.logout()
  banStatus.value = null
  ElMessage.success(t('auth.logoutSuccess'))
  router.push('/')
}

const handleMobileLanguageSwitch = (code) => {
  if (code !== currentLocale.value) {
    localeStore.switchLocale(code)
    const locale = locales.find(l => l.code === code)
    if (locale) {
      ElMessage.success(locale.name)
    }
  }
}

const handleMobileThemeToggle = () => {
  themeStore.toggleTheme()
}
</script>


<style lang="scss" scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

// Header - 三段式布局：Logo | 导航 | 控件
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  border-bottom: 1px solid var(--border-light);
  backdrop-filter: blur(12px);
  
  &__container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
    height: 64px;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 24px;
    
    @media (max-width: 768px) {
      padding: 0 16px;
      gap: 12px;
      // 移动端改为两端布局
      grid-template-columns: auto 1fr;
    }
  }
  
  &__right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    height: 36px;
  }
  
  &__controls {
    display: flex;
    align-items: center;
    gap: 6px;
    height: 36px;
  }
}

// Logo - 固定尺寸容器，避免切换跳动
.logo {
  display: flex;
  align-items: center;
  text-decoration: none;
  flex-shrink: 0;
  justify-self: start;
  
  &__wrapper {
    display: flex;
    align-items: center;
    gap: 10px;
    // 固定高度容器
    height: 36px;
    min-width: 36px;
  }
  
  &__icon {
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
  
  &__text {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    white-space: nowrap;
    
    @media (max-width: 480px) {
      display: none;
    }
  }
  
  &__image {
    // 固定高度，宽度自适应，保持比例
    height: 32px;
    width: auto;
    max-width: 160px;
    object-fit: contain;
    object-position: left center;
    // 平滑过渡，避免切换时跳动
    transition: opacity 0.2s ease;
  }
}

// Navigation - 居中显示，使用胶囊背景
.nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  // 导航容器背景，形成胶囊效果
  background: var(--bg-secondary);
  border-radius: var(--radius-full);
  padding: 4px;
  border: 1px solid var(--border-light);
  
  &--desktop {
    @media (max-width: 768px) {
      display: none;
    }
  }
  
  &__link {
    padding: 6px 14px;
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-full);
    transition: all 0.2s ease;
    white-space: nowrap;
    
    &:hover {
      color: var(--text-primary);
    }
    
    &--active {
      color: var(--text-primary);
      background: var(--bg-card);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }
  }
}

// Desktop only elements
.desktop-only {
  @media (max-width: 768px) {
    display: none !important;
  }
}

// Mobile Menu Toggle (Always visible on mobile)
.mobile-menu-toggle {
  display: none;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  
  @media (max-width: 768px) {
    display: flex;
  }
  
  &:hover {
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
  }
  
  .hamburger {
    position: relative;
    width: 18px;
    height: 2px;
    background: var(--text-primary);
    border-radius: 1px;
    transition: all 0.3s;
    
    &::before,
    &::after {
      content: '';
      position: absolute;
      left: 0;
      width: 18px;
      height: 2px;
      background: var(--text-primary);
      border-radius: 1px;
      transition: all 0.3s;
    }
    
    &::before { top: -6px; }
    &::after { top: 6px; }
  }
  
  &.is-active .hamburger {
    background: transparent;
    
    &::before {
      top: 0;
      transform: rotate(45deg);
    }
    
    &::after {
      top: 0;
      transform: rotate(-45deg);
    }
  }
}

// Mobile Navigation Overlay
.mobile-nav-overlay {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  backdrop-filter: blur(4px);
}

.mobile-nav {
  position: absolute;
  top: 0;
  right: 0;
  width: 280px;
  max-width: 85vw;
  height: 100%;
  background: var(--bg-card);
  border-left: 1px solid var(--border-light);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  &__links {
    flex: 1;
    padding: 12px;
    overflow-y: auto;
  }
  
  &__section-title {
    font-size: 10px;
    font-weight: 600;
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 12px 10px 8px;
    margin-top: 4px;
    
    &:first-child {
      margin-top: 0;
    }
  }
  
  &__setting-group {
    margin-bottom: 16px;
  }
  
  &__setting-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 10px;
    padding: 0 4px;
    
    svg {
      flex-shrink: 0;
      opacity: 0.7;
    }
  }
  
  &__link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition: all 0.15s ease;
    margin-bottom: 2px;
    background: none;
    border: none;
    width: 100%;
    cursor: pointer;
    text-align: left;
    
    svg { 
      flex-shrink: 0;
      width: 18px;
      height: 18px;
    }
    
    &:hover {
      color: var(--text-primary);
      background: var(--bg-secondary);
    }
    
    &--active {
      color: var(--accent-primary);
      background: rgba(var(--accent-primary-rgb), 0.08);
      
      svg { color: var(--accent-primary); }
    }
    
    &--primary {
      background: var(--text-primary);
      color: var(--bg-card);
      margin-top: 4px;
      
      &:hover {
        opacity: 0.9;
        color: var(--bg-card);
        background: var(--text-primary);
      }
      
      svg { color: var(--bg-card); }
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
    margin: 12px 0;
  }
  
  &__user {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--border-light);
    background: var(--bg-secondary);
    flex-shrink: 0;
  }
  
  &__avatar {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-primary);
    color: var(--text-inverse);
    font-size: var(--text-base);
    font-weight: 600;
    border-radius: 50%;
    flex-shrink: 0;
    
    &--banned { background: #ef4444; }
  }
  
  &__user-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }
  
  &__username {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
  }
  
  &__ban-tag {
    font-size: 11px;
    color: #ef4444;
    font-weight: 500;
  }
}

// Mobile Language Switcher
.mobile-lang-switcher {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mobile-lang-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
  text-align: left;
  
  &:hover {
    background: var(--bg-tertiary);
  }
  
  &.is-active {
    background: rgba(var(--accent-primary-rgb), 0.08);
    border-color: rgba(var(--accent-primary-rgb), 0.3);
    
    .mobile-lang-btn__name { 
      color: var(--accent-primary); 
      font-weight: 600; 
    }
  }
  
  &__name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  &__check {
    color: var(--accent-primary);
    flex-shrink: 0;
  }
}

// Mobile Theme Button
.mobile-theme-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  
  &:hover {
    background: var(--bg-tertiary);
  }
  
  svg {
    flex-shrink: 0;
    color: var(--text-secondary);
  }
}

// Slide transition
.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.3s ease;
  
  .mobile-nav { transition: transform 0.3s ease; }
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  
  .mobile-nav { transform: translateX(100%); }
}

// Auth Capsule - 现代胶囊设计
.auth-capsule {
  display: inline-flex;
  align-items: center;
  height: 36px;
  border-radius: var(--radius-full);
  overflow: hidden;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  flex-shrink: 0;
  margin: 0;
  vertical-align: middle;
  box-sizing: border-box;
  
  &__btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 14px;
    height: 100%;
    font-size: 13px;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.2s ease;
    white-space: nowrap;
    line-height: 1;
    
    &--login {
      color: var(--text-secondary);
      background: transparent;
      
      &:hover {
        color: var(--text-primary);
      }
    }
    
    &--register {
      color: var(--text-inverse);
      background: var(--text-primary);
      border-radius: var(--radius-full);
      margin: 3px;
      padding: 0 12px;
      height: calc(100% - 6px);
      
      &:hover {
        opacity: 0.9;
      }
    }
  }
}

// User Dropdown
.user-dropdown {
  position: relative;
  
  &__menu {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    min-width: 160px;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    padding: 4px;
    z-index: 1000;
  }
  
  &__item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 10px;
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    
    svg {
      flex-shrink: 0;
      color: var(--text-tertiary);
      width: 15px;
      height: 15px;
    }
    
    &:hover {
      background: var(--bg-secondary);
      
      svg { color: var(--text-secondary); }
    }
    
    &--warn {
      color: #f59e0b;
      
      svg { color: #f59e0b; }
      
      &:hover {
        background: rgba(245, 158, 11, 0.08);
      }
    }
    
    &--danger {
      color: #ef4444;
      
      svg { color: #ef4444; }
      
      &:hover {
        background: rgba(239, 68, 68, 0.08);
      }
    }
  }
  
  &__divider {
    height: 1px;
    background: var(--border-light);
    margin: 4px 0;
  }
}

// User Menu Button - 统一36px高度
.user-menu {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px 3px 3px;
  height: 36px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0;
  vertical-align: middle;
  box-sizing: border-box;
  line-height: 1;
  
  &:hover { 
    background: var(--bg-tertiary);
    border-color: var(--border-medium);
  }
  
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
    line-height: 1;
    
    &--banned { 
      background: linear-gradient(135deg, #ef4444, #dc2626);
    }
  }
  
  &__name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    line-height: 1;
  }
  
  &__arrow { 
    color: var(--text-tertiary);
    transition: transform 0.2s ease;
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    
    &.is-open {
      transform: rotate(180deg);
    }
  }
}

// Dropdown animation
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

// Ban Badge
.ban-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  font-size: var(--text-xs);
  font-weight: 500;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover { background: rgba(239, 68, 68, 0.2); }
}

// Footer
.footer {
  background: var(--bg-card);
  border-top: 1px solid var(--border-light);
  
  &__container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
    text-align: center;
  }
  
  &__text {
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }
}

// Main Content
.main-content {
  flex: 1;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 24px;
  
  @media (max-width: 768px) {
    padding: 24px 16px;
  }
}

// Dialog
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  padding: 20px;
}

.dialog {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-light);
  }
  
  &__title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }
  
  &__close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    font-size: 24px;
    color: var(--text-tertiary);
    cursor: pointer;
    border-radius: var(--radius-md);
    
    &:hover {
      background: var(--bg-secondary);
      color: var(--text-primary);
    }
  }
  
  &__body {
    padding: 24px;
    overflow-y: auto;
  }
  
  &__footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid var(--border-light);
  }
}

// Ban Info
.ban-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  &__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
  }
  
  &__label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }
  
  &__value {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-primary);
    
    &--danger { color: #ef4444; }
    &--warning { color: #f59e0b; }
    &--success { color: #10b981; }
  }
}

// Appeal Form
.appeal-form {
  margin-top: 16px;
  
  &__title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 16px 0 12px;
  }
}

.form-divider {
  height: 1px;
  background: var(--border-light);
  margin: 16px 0;
}

.form-textarea {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-primary);
  resize: vertical;
  min-height: 100px;
  font-family: inherit;
  
  &::placeholder { color: var(--text-tertiary); }
  &:focus {
    outline: none;
    border-color: var(--accent-primary);
  }
}

// Buttons
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover:not(:disabled) { opacity: 0.9; }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
  
  &--secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    
    &:hover { background: var(--bg-tertiary); }
  }
}
</style>
