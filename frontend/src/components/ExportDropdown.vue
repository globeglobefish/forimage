<template>
  <el-dropdown trigger="click" @command="handleExport" :disabled="disabled">
    <button class="btn btn--secondary" :class="btnClass" :disabled="disabled">
      <svg v-if="loading" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="32"/>
      </svg>
      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 16v1a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-1"/>
        <polyline points="7,10 12,15 17,10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      {{ loading ? $t('download.downloading') : $t('export.title') }}
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6,9 12,15 18,9"/>
      </svg>
    </button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="text">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          {{ $t('export.asText') }}
        </el-dropdown-item>
        <el-dropdown-item command="markdown">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <path d="M9 15l2-2 2 2"/>
            <path d="M9 11h6"/>
          </svg>
          {{ $t('export.asMarkdown') }}
        </el-dropdown-item>
        <el-dropdown-item command="html">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16,18 22,12 16,6"/>
            <polyline points="8,6 2,12 8,18"/>
          </svg>
          {{ $t('export.asHtml') }}
        </el-dropdown-item>
        <el-dropdown-item divided command="zip">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7,10 12,15 17,10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          {{ $t('export.asZip') }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const props = defineProps({
  // 图片列表（用于导出文本/markdown）
  images: {
    type: Array,
    default: () => []
  },
  // 选中的图片ID列表（批量模式）
  selectedIds: {
    type: Array,
    default: () => []
  },
  // 相册ID（用于打包下载整个相册）
  albumId: {
    type: [Number, String],
    default: null
  },
  // 相册名称（用于文件命名）
  albumName: {
    type: String,
    default: 'images'
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 按钮额外样式类
  btnClass: {
    type: String,
    default: ''
  },
  // 是否是画廊模式（使用不同的下载API）
  isGallery: {
    type: Boolean,
    default: false
  }
})

const { t } = useI18n()
const loading = ref(false)

// 获取完整URL
const getFullUrl = (image) => {
  return image.url.startsWith('http') ? image.url : window.location.origin + image.url
}

// 获取要导出的图片列表
const getExportImages = () => {
  if (props.selectedIds.length > 0) {
    return props.images.filter(img => props.selectedIds.includes(img.id))
  }
  return props.images
}

// 导出为纯文本（直链，一行一个）
const exportAsText = () => {
  const images = getExportImages()
  if (images.length === 0) {
    ElMessage.warning(t('export.noImages'))
    return
  }
  
  const text = images.map(img => getFullUrl(img)).join('\n')
  copyToClipboard(text)
  ElMessage.success(t('export.textCopied', { count: images.length }))
}

// 导出为Markdown
const exportAsMarkdown = () => {
  const images = getExportImages()
  if (images.length === 0) {
    ElMessage.warning(t('export.noImages'))
    return
  }
  
  const markdown = images.map(img => {
    const name = img.title || img.original_filename
    return `![${name}](${getFullUrl(img)})`
  }).join('\n')
  copyToClipboard(markdown)
  ElMessage.success(t('export.markdownCopied', { count: images.length }))
}

// 导出为HTML
const exportAsHtml = () => {
  const images = getExportImages()
  if (images.length === 0) {
    ElMessage.warning(t('export.noImages'))
    return
  }
  
  const html = images.map(img => {
    const name = img.title || img.original_filename
    return `<img src="${getFullUrl(img)}" alt="${name}" />`
  }).join('\n')
  copyToClipboard(html)
  ElMessage.success(t('export.htmlCopied', { count: images.length }))
}

// 打包下载
const exportAsZip = async () => {
  const images = getExportImages()
  
  // 如果有选中的图片，使用批量下载
  if (props.selectedIds.length > 0) {
    if (props.selectedIds.length > 100) {
      ElMessage.warning(t('download.maxImages'))
      return
    }
    await downloadBatch(props.selectedIds)
    return
  }
  
  // 如果有相册ID，下载整个相册
  if (props.albumId) {
    await downloadAlbum()
    return
  }
  
  // 否则下载当前显示的图片
  if (images.length === 0) {
    ElMessage.warning(t('export.noImages'))
    return
  }
  
  if (images.length > 100) {
    ElMessage.warning(t('download.maxImages'))
    return
  }
  
  await downloadBatch(images.map(img => img.id))
}

// 批量下载
const downloadBatch = async (imageIds) => {
  loading.value = true
  try {
    const response = await api.post('/download/batch', 
      { image_ids: imageIds },
      { responseType: 'blob' }
    )
    
    downloadBlob(response, `${props.albumName}.zip`)
    ElMessage.success(t('download.downloadSuccess'))
  } catch (error) {
    console.error(error)
    ElMessage.error(t('download.downloadError'))
  } finally {
    loading.value = false
  }
}

// 下载相册
const downloadAlbum = async () => {
  loading.value = true
  try {
    // 画廊模式使用不同的API
    const url = props.isGallery 
      ? `/gallery/${props.albumId}/download`
      : `/download/album/${props.albumId}`
    
    const response = await api.get(url, {
      responseType: 'blob'
    })
    
    downloadBlob(response, `${props.albumName}.zip`)
    ElMessage.success(t('download.downloadSuccess'))
  } catch (error) {
    console.error(error)
    if (error.response?.status === 429) {
      ElMessage.error(t('download.rateLimitExceeded'))
    } else {
      ElMessage.error(t('download.downloadError'))
    }
  } finally {
    loading.value = false
  }
}

// 下载blob文件
const downloadBlob = (response, defaultFilename) => {
  const blob = new Blob([response.data], { type: 'application/zip' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  
  const contentDisposition = response.headers['content-disposition']
  let filename = defaultFilename
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^";\n]+)"?/)
    if (match) filename = match[1]
  }
  
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// 复制到剪贴板
const copyToClipboard = async (text) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return
    }
    // Fallback
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    textArea.style.top = '-9999px'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  } catch (err) {
    console.error('Copy failed:', err)
    ElMessage.error(t('error.copyFailed'))
  }
}

// 处理导出命令
const handleExport = (command) => {
  switch (command) {
    case 'text':
      exportAsText()
      break
    case 'markdown':
      exportAsMarkdown()
      break
    case 'html':
      exportAsHtml()
      break
    case 'zip':
      exportAsZip()
      break
  }
}
</script>

<style lang="scss" scoped>
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    &:hover:not(:disabled) { background: var(--bg-tertiary); }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
  }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  
  svg {
    flex-shrink: 0;
  }
}
</style>
