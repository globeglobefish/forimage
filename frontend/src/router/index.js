import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
      },
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { guest: true },
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/Register.vue'),
        meta: { guest: true },
      },
      {
        path: 'verify-email',
        name: 'VerifyEmail',
        component: () => import('@/views/VerifyEmail.vue'),
      },
      {
        path: 'forgot-password',
        name: 'ForgotPassword',
        component: () => import('@/views/ForgotPassword.vue'),
        meta: { guest: true },
      },
      {
        path: 'reset-password',
        name: 'ResetPassword',
        component: () => import('@/views/ResetPassword.vue'),
        meta: { guest: true },
      },
      {
        path: 'my-images',
        name: 'MyImages',
        component: () => import('@/views/MyImages.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'albums',
        name: 'Albums',
        component: () => import('@/views/Albums.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'albums/:id',
        name: 'AlbumDetail',
        component: () => import('@/views/AlbumDetail.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'gallery',
        name: 'Gallery',
        component: () => import('@/views/Gallery.vue'),
      },
      {
        path: 'gallery/:id',
        name: 'GalleryAlbum',
        component: () => import('@/views/GalleryAlbum.vue'),
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
      },
      {
        path: 'images',
        name: 'AdminImages',
        component: () => import('@/views/admin/Images.vue'),
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/Settings.vue'),
      },
      {
        path: 'blacklist',
        name: 'AdminBlacklist',
        component: () => import('@/views/admin/Blacklist.vue'),
      },
      {
        path: 'backup',
        name: 'AdminBackup',
        component: () => import('@/views/admin/Backup.vue'),
      },
      {
        path: 'gallery',
        name: 'AdminGallery',
        component: () => import('@/views/admin/Gallery.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // Try to restore session if not loaded
  if (!userStore.loaded) {
    await userStore.loadUser()
  }
  
  // Check if route requires authentication
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  
  // Check if route requires admin
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    return next({ name: 'Home' })
  }
  
  // Redirect logged in users away from guest-only pages
  if (to.meta.guest && userStore.isLoggedIn) {
    return next({ name: 'Home' })
  }
  
  next()
})

export default router
