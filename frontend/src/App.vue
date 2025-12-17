<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()

onMounted(async () => {
  await siteStore.loadSettings()
  // updatePageMeta is called inside loadSettings
})
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  min-height: 100%;
}

/* Smooth transition for theme changes */
html {
  transition: background-color 0.3s ease, color 0.3s ease;
}
</style>
