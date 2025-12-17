<template>
  <div class="admin-page">
    <h2 class="admin-page__title">{{ $t('admin.settings') }}</h2>
    
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
      
      <!-- Settings Content -->
      <div class="settings-content">
        <!-- General Settings -->
        <div v-show="activeTab === 'general'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('settings.general') }}</h3>
            <p class="section-desc">{{ $t('admin.generalSettingsDesc') }}</p>
          </div>
          
          <div class="settings-card" v-if="settings.general">
            <h4 class="config-title">{{ $t('admin.basicInfo') }}</h4>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('settings.siteName') }}</span>
                <span class="label-hint">{{ $t('admin.siteNameHint') }}</span>
              </label>
              <input v-model="settings.general.site_name" type="text" class="form-input" placeholder="Forimage" />
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('settings.siteTitle') }}</span>
                <span class="label-hint">{{ $t('admin.siteTitleHint') }}</span>
              </label>
              <input v-model="settings.general.site_title" type="text" class="form-input" :placeholder="$t('admin.siteTitlePlaceholder')" />
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('settings.siteDescription') }}</span>
                <span class="label-hint">{{ $t('admin.siteDescriptionHint') }}</span>
              </label>
              <textarea v-model="settings.general.site_description" class="form-input form-textarea" rows="2" :placeholder="$t('admin.siteDescriptionPlaceholder')"></textarea>
            </div>
            
            <div class="form-divider"></div>
            <h4 class="config-title">{{ $t('admin.frontendDisplay') }}</h4>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('settings.siteSlogan') }}</span>
                <span class="label-hint">{{ $t('admin.siteSloganHint') }}</span>
              </label>
              <input v-model="settings.general.site_slogan" type="text" class="form-input" :placeholder="$t('admin.siteSloganPlaceholder')" />
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('settings.siteFooter') }}</span>
                <span class="label-hint">{{ $t('admin.siteFooterHint') }}</span>
              </label>
              <input v-model="settings.general.site_footer" type="text" class="form-input" :placeholder="$t('admin.siteFooterPlaceholder')" />
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.siteUrl') }}</span>
                <span class="label-hint">{{ $t('admin.siteUrlHint') }}</span>
              </label>
              <input v-model="settings.general.site_url" type="text" class="form-input" placeholder="https://example.com" />
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('settings.timezone') }}</span>
                <span class="label-hint">{{ $t('admin.timezoneHint') }}</span>
              </label>
              <select v-model="settings.general.timezone" class="form-input form-select">
                <option value="Asia/Shanghai">{{ $t('admin.timezoneChina') }}</option>
                <option value="Asia/Tokyo">{{ $t('admin.timezoneJapan') }}</option>
                <option value="Asia/Singapore">{{ $t('admin.timezoneSingapore') }}</option>
                <option value="Asia/Hong_Kong">{{ $t('admin.timezoneHongKong') }}</option>
                <option value="UTC">{{ $t('admin.timezoneUTC') }}</option>
                <option value="America/New_York">{{ $t('admin.timezoneUSEast') }}</option>
                <option value="America/Los_Angeles">{{ $t('admin.timezoneUSWest') }}</option>
                <option value="Europe/London">{{ $t('admin.timezoneUK') }}</option>
                <option value="Europe/Paris">{{ $t('admin.timezoneEurope') }}</option>
              </select>
            </div>
            
            <div class="form-divider"></div>
            <h4 class="config-title">{{ $t('admin.logoAndIcon') }}</h4>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.siteLogo') }}</span>
                <span class="label-hint">{{ $t('admin.siteLogoHint') }}</span>
              </label>
              <div class="logo-input-group">
                <input v-model="settings.general.site_logo" type="text" class="form-input" :placeholder="$t('admin.siteLogoPlaceholder')" />
                <div v-if="settings.general.site_logo" class="logo-preview">
                  <img :src="settings.general.site_logo" :alt="$t('admin.logoPreview')" @error="handleLogoError" />
                </div>
              </div>
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.siteLogoDark') }}</span>
                <span class="label-hint">{{ $t('admin.siteLogoDarkHint') }}</span>
              </label>
              <div class="logo-input-group">
                <input v-model="settings.general.site_logo_dark" type="text" class="form-input" :placeholder="$t('admin.siteLogoDarkPlaceholder')" />
                <div v-if="settings.general.site_logo_dark" class="logo-preview logo-preview--dark">
                  <img :src="settings.general.site_logo_dark" :alt="$t('admin.logoDarkPreview')" @error="handleLogoDarkError" />
                </div>
              </div>
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.favicon') }}</span>
                <span class="label-hint">{{ $t('admin.faviconHint') }}</span>
              </label>
              <div class="logo-input-group">
                <input v-model="settings.general.site_favicon" type="text" class="form-input" :placeholder="$t('admin.faviconPlaceholder')" />
                <div v-if="settings.general.site_favicon" class="favicon-preview">
                  <img :src="settings.general.site_favicon" :alt="$t('admin.faviconPreview')" @error="handleFaviconError" />
                </div>
              </div>
            </div>
            
            <div class="form-divider"></div>
            <h4 class="config-title">{{ $t('admin.featureToggles') }}</h4>
            
            <div class="form-row form-row--switch">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.enableRegistration') }}</span>
                <span class="label-hint">{{ $t('admin.enableRegistrationHint') }}</span>
              </label>
              <label class="switch">
                <input type="checkbox" v-model="settings.general.enable_registration" />
                <span class="switch__slider"></span>
              </label>
            </div>
            
            <div class="form-row form-row--switch">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.enableGuestUpload') }}</span>
                <span class="label-hint">{{ $t('admin.enableGuestUploadHint') }}</span>
              </label>
              <label class="switch">
                <input type="checkbox" v-model="settings.general.enable_guest_upload" />
                <span class="switch__slider"></span>
              </label>
            </div>
            
          </div>
        </div>
        
        <!-- Upload Settings -->
        <div v-show="activeTab === 'upload'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('settings.upload') }}</h3>
            <p class="section-desc">{{ $t('admin.uploadSettingsDesc') }}</p>
          </div>
          
          <div class="settings-card" v-if="settings.upload">
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.guestSizeLimit') }}</span>
                <span class="label-hint">{{ $t('admin.guestSizeLimitHint') }}</span>
              </label>
              <div class="input-group">
                <input v-model.number="guestSizeMB" type="number" class="form-input" min="1" max="100" />
                <span class="input-group__suffix">MB</span>
              </div>
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.userSizeLimit') }}</span>
                <span class="label-hint">{{ $t('admin.userSizeLimitHint') }}</span>
              </label>
              <div class="input-group">
                <input v-model.number="userSizeMB" type="number" class="form-input" min="1" max="100" />
                <span class="input-group__suffix">MB</span>
              </div>
            </div>
            
            <div class="form-divider"></div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.allowedFormats') }}</span>
                <span class="label-hint">{{ $t('admin.allowedFormatsHint') }}</span>
              </label>
              <input v-model="settings.upload.allowed_extensions" type="text" class="form-input" placeholder="png,jpg,jpeg,gif,webp" />
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.compressionQuality') }}</span>
                <span class="label-hint">{{ $t('admin.compressionQualityHint') }}</span>
              </label>
              <div class="slider-input">
                <input 
                  type="range" 
                  v-model.number="settings.upload.compression_quality" 
                  min="10" 
                  max="100" 
                  class="slider"
                />
                <span class="slider-value">{{ settings.upload.compression_quality }}%</span>
              </div>
            </div>
            
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.maxDimension') }}</span>
                <span class="label-hint">{{ $t('admin.maxDimensionHint') }}</span>
              </label>
              <div class="input-group">
                <input v-model.number="settings.upload.max_dimension" type="number" class="form-input" min="0" placeholder="4096" />
                <span class="input-group__suffix">{{ $t('admin.pixels') }}</span>
              </div>
            </div>
            
          </div>
        </div>
        
        <!-- Storage Settings -->
        <div v-show="activeTab === 'storage'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('settings.storage') }}</h3>
            <p class="section-desc">{{ $t('admin.storageSettingsDesc') }}</p>
          </div>
          
          <div class="settings-card" v-if="settings.storage">
            <div class="form-row">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.storageType') }}</span>
                <span class="label-hint">{{ $t('admin.storageTypeHint') }}</span>
              </label>
              <div class="radio-group">
                <label class="radio-item" :class="{ 'is-active': settings.storage.type === 'local' }">
                  <input type="radio" v-model="settings.storage.type" value="local" />
                  <span class="radio-item__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                    </svg>
                  </span>
                  <span class="radio-item__text">{{ $t('admin.localStorage') }}</span>
                </label>
                <label class="radio-item" :class="{ 'is-active': settings.storage.type === 's3c' }">
                  <input type="radio" v-model="settings.storage.type" value="s3c" />
                  <span class="radio-item__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
                    </svg>
                  </span>
                  <span class="radio-item__text">{{ $t('admin.s3Compatible') }}</span>
                </label>
                <label class="radio-item" :class="{ 'is-active': settings.storage.type === 'oss' }">
                  <input type="radio" v-model="settings.storage.type" value="oss" />
                  <span class="radio-item__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
                    </svg>
                  </span>
                  <span class="radio-item__text">{{ $t('admin.aliOss') }}</span>
                </label>
                <label class="radio-item" :class="{ 'is-active': settings.storage.type === 'cos' }">
                  <input type="radio" v-model="settings.storage.type" value="cos" />
                  <span class="radio-item__icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
                    </svg>
                  </span>
                  <span class="radio-item__text">{{ $t('admin.tencentCos') }}</span>
                </label>
              </div>
            </div>
            
            <!-- Local Storage Config -->
            <template v-if="settings.storage.type === 'local'">
              <div class="form-divider"></div>
              <div class="config-section">
                <h4 class="config-title">{{ $t('admin.localStorageConfig') }}</h4>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.localPublicUrl') }}</span>
                    <span class="label-hint">{{ $t('admin.localPublicUrlHint') }}</span>
                  </label>
                  <input v-model="settings.storage.local_public_url" type="text" class="form-input" placeholder="https://cdn.example.com" />
                </div>
              </div>
            </template>
            
            <!-- S3 Compatible Config -->
            <template v-if="settings.storage.type === 's3c'">
              <div class="form-divider"></div>
              <div class="config-section">
                <h4 class="config-title">{{ $t('admin.s3cConfig') }}</h4>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.s3cProvider') }}</span>
                    <span class="label-hint">{{ $t('admin.s3cProviderHint') }}</span>
                  </label>
                  <select v-model="settings.storage.s3c_provider" class="form-input form-select" @change="onS3cProviderChange">
                    <option value="aws">AWS S3</option>
                    <option value="r2">Cloudflare R2</option>
                    <option value="cos">腾讯云 COS (S3模式)</option>
                    <option value="minio">MinIO</option>
                    <option value="b2">Backblaze B2</option>
                    <option value="spaces">DigitalOcean Spaces</option>
                    <option value="custom">{{ $t('admin.s3cCustom') }}</option>
                  </select>
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.accessKeyId') }}</span></label>
                  <input v-model="settings.storage.s3c_access_key_id" type="text" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.secretAccessKey') }}</span></label>
                  <input v-model="settings.storage.s3c_secret_access_key" type="password" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.bucketName') }}</span></label>
                  <input v-model="settings.storage.s3c_bucket_name" type="text" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.s3cEndpoint') }}</span>
                    <span class="label-hint">{{ $t('admin.s3cEndpointHint') }}</span>
                  </label>
                  <input v-model="settings.storage.s3c_endpoint_url" type="text" class="form-input" :placeholder="s3cEndpointPlaceholder" />
                </div>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.region') }}</span>
                    <span class="label-hint">{{ $t('admin.s3cRegionHint') }}</span>
                  </label>
                  <input v-model="settings.storage.s3c_region" type="text" class="form-input" :placeholder="s3cRegionPlaceholder" />
                </div>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.publicUrl') }}</span>
                    <span class="label-hint">{{ $t('admin.s3cPublicUrlHint') }}</span>
                  </label>
                  <input v-model="settings.storage.s3c_public_url" type="text" class="form-input" placeholder="https://images.example.com" />
                </div>
              </div>
            </template>
            
            <!-- OSS Config -->
            <template v-if="settings.storage.type === 'oss'">
              <div class="form-divider"></div>
              <div class="config-section">
                <h4 class="config-title">{{ $t('admin.ossConfig') }}</h4>
                <p class="config-desc">{{ $t('admin.ossConfigDesc') }}</p>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.accessKeyId') }}</span></label>
                  <input v-model="settings.storage.oss_access_key_id" type="text" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.accessKeySecret') }}</span></label>
                  <input v-model="settings.storage.oss_access_key_secret" type="password" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.bucketName') }}</span></label>
                  <input v-model="settings.storage.oss_bucket_name" type="text" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">{{ $t('admin.endpoint') }}</span></label>
                  <input v-model="settings.storage.oss_endpoint" type="text" class="form-input" placeholder="oss-cn-hangzhou.aliyuncs.com" />
                </div>
              </div>
            </template>
            
            <!-- COS Config -->
            <template v-if="settings.storage.type === 'cos'">
              <div class="form-divider"></div>
              <div class="config-section">
                <h4 class="config-title">{{ $t('admin.cosConfig') }}</h4>
                <p class="config-desc">{{ $t('admin.cosConfigDesc') }}</p>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">SecretId</span></label>
                  <input v-model="settings.storage.cos_secret_id" type="text" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label"><span class="label-text">SecretKey</span></label>
                  <input v-model="settings.storage.cos_secret_key" type="password" class="form-input" />
                </div>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.bucketName') }}</span>
                    <span class="label-hint">{{ $t('admin.cosBucketHint') }}</span>
                  </label>
                  <input v-model="settings.storage.cos_bucket_name" type="text" class="form-input" placeholder="mybucket-1250000000" />
                </div>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.region') }}</span>
                    <span class="label-hint">{{ $t('admin.cosRegionHint') }}</span>
                  </label>
                  <input v-model="settings.storage.cos_region" type="text" class="form-input" placeholder="ap-guangzhou" />
                </div>
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.publicUrl') }}</span>
                    <span class="label-hint">{{ $t('admin.cosPublicUrlHint') }}</span>
                  </label>
                  <input v-model="settings.storage.cos_public_url" type="text" class="form-input" placeholder="https://images.example.com" />
                </div>
              </div>
            </template>
          </div>
        </div>
        
        <!-- Audit Settings -->
        <div v-show="activeTab === 'audit'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('settings.audit') }}</h3>
            <p class="section-desc">{{ $t('admin.auditSettingsDesc') }}</p>
          </div>
          
          <div class="settings-card" v-if="settings.audit">
            <div class="form-row form-row--switch">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.enableAudit') }}</span>
                <span class="label-hint">{{ $t('admin.enableAuditHint') }}</span>
              </label>
              <label class="switch">
                <input type="checkbox" v-model="settings.audit.enabled" />
                <span class="switch__slider"></span>
              </label>
            </div>
            
            <template v-if="settings.audit.enabled">
              <div class="form-divider"></div>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.auditProvider') }}</span>
                </label>
                <select v-model="settings.audit.provider" class="form-input form-select">
                  <option value="">{{ $t('admin.selectProvider') }}</option>
                  <option value="aliyun">{{ $t('admin.aliyunAudit') }}</option>
                  <option value="tencent">{{ $t('admin.tencentAudit') }}</option>
                </select>
              </div>
              
              <!-- 腾讯云提示 -->
              <div v-if="settings.audit.provider === 'tencent'" class="form-row">
                <el-alert type="info" :closable="false" show-icon>
                  {{ $t('admin.tencentAuditHint') }}
                </el-alert>
              </div>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.apiKey') }}</span>
                  <span class="label-hint" v-if="settings.audit.provider === 'aliyun'">{{ $t('admin.apiKeyHintAliyun') }}</span>
                  <span class="label-hint" v-else-if="settings.audit.provider === 'tencent'">{{ $t('admin.apiKeyHintTencent') }}</span>
                </label>
                <input v-model="settings.audit.api_key" type="text" class="form-input" />
              </div>
              
              <div class="form-row">
                <label class="form-label"><span class="label-text">{{ $t('admin.apiSecret') }}</span></label>
                <input v-model="settings.audit.api_secret" type="password" class="form-input" />
              </div>
              
              <!-- 腾讯云 COS Bucket 和 Region 配置 -->
              <template v-if="settings.audit.provider === 'tencent'">
                <div class="form-divider"></div>
                <h4 class="config-title">{{ $t('admin.tencentCosConfig') }}</h4>
                
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.tencentAuditBucket') }}</span>
                    <span class="label-hint">{{ $t('admin.tencentAuditBucketHint') }}</span>
                  </label>
                  <input v-model="settings.audit.tencent_bucket" type="text" class="form-input" placeholder="bucket-1250000000" />
                </div>
                
                <div class="form-row">
                  <label class="form-label">
                    <span class="label-text">{{ $t('admin.tencentAuditRegion') }}</span>
                    <span class="label-hint">{{ $t('admin.tencentAuditRegionHint') }}</span>
                  </label>
                  <input v-model="settings.audit.tencent_region" type="text" class="form-input" placeholder="ap-guangzhou" />
                </div>
              </template>
              
              <div class="form-divider"></div>
              
              <div class="form-row form-row--switch">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.autoReject') }}</span>
                  <span class="label-hint">{{ $t('admin.autoRejectHint') }}</span>
                </label>
                <label class="switch">
                  <input type="checkbox" v-model="settings.audit.auto_reject" />
                  <span class="switch__slider"></span>
                </label>
              </div>
              
              <div class="form-divider"></div>
              <h4 class="config-title">{{ $t('admin.violationImageHandling') }}</h4>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.violationImage') }}</span>
                  <span class="label-hint">{{ $t('admin.violationImageHint') }}</span>
                </label>
                <div class="logo-input-group">
                  <input v-model="settings.audit.violation_image" type="text" class="form-input" :placeholder="$t('admin.violationImagePlaceholder')" />
                  <div v-if="settings.audit.violation_image" class="logo-preview">
                    <img :src="settings.audit.violation_image" :alt="$t('admin.violationImagePreview')" @error="handleViolationImageError" />
                  </div>
                </div>
              </div>
              
            </template>
          </div>
        </div>
        
        <!-- Email Settings -->
        <div v-show="activeTab === 'email'" class="settings-section">
          <div class="section-header">
            <h3 class="section-title">{{ $t('settings.email') }}</h3>
            <p class="section-desc">{{ $t('admin.emailSettingsDesc') }}</p>
          </div>
          
          <div class="settings-card" v-if="settings.email">
            <div class="form-row form-row--switch">
              <label class="form-label">
                <span class="label-text">{{ $t('admin.enableEmail') }}</span>
                <span class="label-hint">{{ $t('admin.enableEmailHint') }}</span>
              </label>
              <label class="switch">
                <input type="checkbox" v-model="settings.email.enabled" />
                <span class="switch__slider"></span>
              </label>
            </div>
            
            <template v-if="settings.email.enabled">
              <div class="form-divider"></div>
              <h4 class="config-title">{{ $t('admin.smtpConfig') }}</h4>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.smtpHost') }}</span>
                  <span class="label-hint">{{ $t('admin.smtpHostHint') }}</span>
                </label>
                <input v-model="settings.email.smtp_host" type="text" class="form-input" :placeholder="$t('admin.smtpHostPlaceholder')" />
              </div>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.smtpPort') }}</span>
                  <span class="label-hint">{{ $t('admin.smtpPortHint') }}</span>
                </label>
                <input v-model.number="settings.email.smtp_port" type="number" class="form-input" :placeholder="$t('admin.smtpPortPlaceholder')" />
              </div>
              
              <div class="form-row form-row--switch">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.smtpSsl') }}</span>
                  <span class="label-hint">{{ $t('admin.smtpSslHint') }}</span>
                </label>
                <label class="switch">
                  <input type="checkbox" v-model="settings.email.smtp_ssl" />
                  <span class="switch__slider"></span>
                </label>
              </div>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.smtpUser') }}</span>
                  <span class="label-hint">{{ $t('admin.smtpUserHint') }}</span>
                </label>
                <input v-model="settings.email.smtp_user" type="text" class="form-input" :placeholder="$t('admin.smtpUserPlaceholder')" />
              </div>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.smtpPassword') }}</span>
                  <span class="label-hint">{{ $t('admin.smtpPasswordHint') }}</span>
                </label>
                <input v-model="settings.email.smtp_password" type="password" class="form-input" :placeholder="$t('admin.smtpPasswordPlaceholder')" />
              </div>
              
              <div class="form-divider"></div>
              <h4 class="config-title">{{ $t('admin.senderInfo') }}</h4>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.fromAddress') }}</span>
                  <span class="label-hint">{{ $t('admin.fromAddressHint') }}</span>
                </label>
                <input v-model="settings.email.from_address" type="email" class="form-input" :placeholder="$t('admin.fromAddressPlaceholder')" />
              </div>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.fromName') }}</span>
                  <span class="label-hint">{{ $t('admin.fromNameHint') }}</span>
                </label>
                <input v-model="settings.email.from_name" type="text" class="form-input" :placeholder="$t('admin.fromNamePlaceholder')" />
              </div>
              
              <div class="form-divider"></div>
              <h4 class="config-title">{{ $t('admin.connectionTest') }}</h4>
              
              <div class="form-row">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.testEmail') }}</span>
                  <span class="label-hint">{{ $t('admin.testEmailHint') }}</span>
                </label>
                <div class="test-email-group">
                  <input v-model="testEmail" type="email" class="form-input" :placeholder="$t('admin.testEmailPlaceholder')" />
                  <button class="btn btn--secondary" @click="sendTestEmail" :disabled="testingEmail">
                    <span v-if="testingEmail" class="btn-loader"></span>
                    {{ testingEmail ? $t('admin.sending') : $t('admin.sendTest') }}
                  </button>
                </div>
              </div>
              
              <div class="form-divider"></div>
              <h4 class="config-title">{{ $t('admin.emailTemplates') }}</h4>
              <p class="template-hint">{{ $t('admin.templateVariables') }}：<code v-pre>{{site_name}}</code> <code v-pre>{{username}}</code> <code v-pre>{{verify_url}}</code> <code v-pre>{{reset_url}}</code></p>
              
              <div class="template-cards">
                <div class="template-card">
                  <div class="template-card__header">
                    <span class="template-card__title">📧 {{ $t('admin.emailVerification') }}</span>
                    <div class="template-card__actions">
                      <button class="btn btn--text btn--sm" @click="openTemplateEditor('verify')">{{ $t('admin.editTemplate') }}</button>
                      <button class="btn btn--text btn--sm" @click="resetTemplate('verify')">{{ $t('admin.resetTemplate') }}</button>
                    </div>
                  </div>
                  <div class="template-card__preview">
                    <div class="preview-label">{{ $t('admin.templateSubject') }}：</div>
                    <div class="preview-value">{{ settings.email.template_verify_subject }}</div>
                  </div>
                </div>
                
                <div class="template-card">
                  <div class="template-card__header">
                    <span class="template-card__title">🔑 {{ $t('admin.passwordReset') }}</span>
                    <div class="template-card__actions">
                      <button class="btn btn--text btn--sm" @click="openTemplateEditor('reset')">{{ $t('admin.editTemplate') }}</button>
                      <button class="btn btn--text btn--sm" @click="resetTemplate('reset')">{{ $t('admin.resetTemplate') }}</button>
                    </div>
                  </div>
                  <div class="template-card__preview">
                    <div class="preview-label">{{ $t('admin.templateSubject') }}：</div>
                    <div class="preview-value">{{ settings.email.template_reset_subject }}</div>
                  </div>
                </div>
              </div>
              
            </template>
          </div>
        </div>
        
        <!-- Template Editor Modal -->
        <div v-if="editingTemplate" class="modal-overlay" @click.self="closeTemplateEditor">
          <div class="modal-content template-editor">
            <div class="modal-header">
              <h3>{{ editingTemplate === 'verify' ? $t('admin.editVerifyTemplate') : $t('admin.editResetTemplate') }}</h3>
              <button class="modal-close" @click="closeTemplateEditor">&times;</button>
            </div>
            <div class="modal-body">
              <div class="form-row" style="grid-template-columns: 1fr;">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.emailSubject') }}</span>
                </label>
                <input 
                  v-model="settings.email[`template_${editingTemplate}_subject`]" 
                  type="text" 
                  class="form-input" 
                />
              </div>
              <div class="form-row" style="grid-template-columns: 1fr; margin-top: 16px;">
                <label class="form-label">
                  <span class="label-text">{{ $t('admin.emailBody') }}</span>
                  <span class="label-hint">{{ $t('admin.emailBodyHint') }}</span>
                </label>
                <textarea 
                  v-model="settings.email[`template_${editingTemplate}_body`]" 
                  class="form-input form-textarea template-textarea"
                  rows="15"
                ></textarea>
              </div>
              <div class="variable-hints">
                <span class="hint-title">{{ $t('admin.templateVariables') }}：</span>
                <code v-pre>{{site_name}}</code> - {{ $t('settings.siteName') }}
                <code v-pre>{{username}}</code> - {{ $t('auth.username') }}
                <template v-if="editingTemplate === 'verify'">
                  <code v-pre>{{verify_url}}</code> - {{ $t('admin.verifyUrl') }}
                </template>
                <template v-else>
                  <code v-pre>{{reset_url}}</code> - {{ $t('admin.resetUrl') }}
                </template>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn--secondary" @click="closeTemplateEditor">{{ $t('common.close') }}</button>
            </div>
          </div>
        </div>
        
        <!-- Save Button -->
        <div class="settings-actions">
          <button class="btn btn--primary btn--lg" @click="saveSettings" :disabled="saving">
            <svg v-if="!saving" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
              <polyline points="17,21 17,13 7,13 7,21"/><polyline points="7,3 7,8 15,8"/>
            </svg>
            <span v-if="saving" class="btn-loader"></span>
            {{ saving ? $t('admin.saving') : $t('admin.saveChanges') }}
          </button>
          <span class="save-hint">{{ $t('admin.saveHint') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import api from '@/api'

const { t } = useI18n()

const activeTab = ref('general')
const saving = ref(false)

const tabs = computed(() => [
  { key: 'general', label: t('settings.general'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
  { key: 'upload', label: t('settings.upload'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>' },
  { key: 'storage', label: t('settings.storage'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>' },
  { key: 'audit', label: t('settings.audit'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' },
  { key: 'email', label: t('settings.email'), icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>' },
])

const settings = reactive({
  general: { 
    site_name: '', 
    site_title: '',
    site_description: '', 
    site_slogan: '',
    site_footer: '',
    site_url: '',
    site_logo: '', 
    site_logo_dark: '',
    site_favicon: '',
    timezone: 'Asia/Shanghai',
    enable_registration: true, 
    enable_guest_upload: true 
  },
  upload: { max_size_guest: 5242880, max_size_user: 10485760, allowed_extensions: 'png,jpg,jpeg,gif,webp', compression_quality: 85, max_dimension: 0 },
  storage: { 
    type: 'local', 
    // Local storage
    local_public_url: '',
    // S3-Compatible (unified)
    s3c_provider: 'custom',
    s3c_access_key_id: '', 
    s3c_secret_access_key: '', 
    s3c_bucket_name: '', 
    s3c_endpoint_url: '', 
    s3c_region: '', 
    s3c_public_url: '',
    // Aliyun OSS (native)
    oss_access_key_id: '', 
    oss_access_key_secret: '', 
    oss_bucket_name: '', 
    oss_endpoint: '',
    // Tencent COS (native)
    cos_secret_id: '',
    cos_secret_key: '',
    cos_bucket_name: '',
    cos_region: '',
    cos_public_url: '',
  },
  audit: { enabled: false, provider: '', api_key: '', api_secret: '', auto_reject: false, violation_image: '', tencent_bucket: '', tencent_region: '' },
  email: { 
    enabled: false, 
    smtp_host: '', 
    smtp_port: 587, 
    smtp_user: '', 
    smtp_password: '', 
    smtp_ssl: false,
    from_address: '', 
    from_name: 'Forimage',
    template_verify_subject: '[{{site_name}}] 验证您的邮箱',
    template_verify_body: '',
    template_reset_subject: '[{{site_name}}] 重置密码',
    template_reset_body: ''
  },
})

// Email test
const testEmail = ref('')
const testingEmail = ref(false)
const editingTemplate = ref(null) // 'verify' or 'reset'

const guestSizeMB = computed({
  get: () => Math.round(settings.upload.max_size_guest / 1048576),
  set: (v) => { settings.upload.max_size_guest = v * 1048576 }
})

const userSizeMB = computed({
  get: () => Math.round(settings.upload.max_size_user / 1048576),
  set: (v) => { settings.upload.max_size_user = v * 1048576 }
})

// S3 Compatible provider placeholders
const s3cEndpointPlaceholder = computed(() => {
  const provider = settings.storage.s3c_provider
  const placeholders = {
    'aws': '留空使用默认AWS端点',
    'r2': 'https://<account_id>.r2.cloudflarestorage.com',
    'cos': 'https://cos.<region>.myqcloud.com',
    'minio': 'https://minio.example.com:9000',
    'b2': 'https://s3.<region>.backblazeb2.com',
    'spaces': 'https://<region>.digitaloceanspaces.com',
    'custom': 'https://s3.example.com',
  }
  return placeholders[provider] || placeholders['custom']
})

const s3cRegionPlaceholder = computed(() => {
  const provider = settings.storage.s3c_provider
  const placeholders = {
    'aws': 'us-east-1',
    'r2': 'auto',
    'cos': 'ap-guangzhou',
    'minio': 'us-east-1',
    'b2': 'us-west-004',
    'spaces': 'nyc3',
    'custom': 'us-east-1',
  }
  return placeholders[provider] || placeholders['custom']
})

const onS3cProviderChange = () => {
  // Auto-fill region for R2
  if (settings.storage.s3c_provider === 'r2' && !settings.storage.s3c_region) {
    settings.storage.s3c_region = 'auto'
  }
}

const loadSettings = async () => {
  try {
    const response = await api.get('/admin/settings')
    for (const group of response.data) {
      if (!settings[group.category]) continue
      for (const setting of group.settings) {
        const key = setting.key.replace(`${group.category}_`, '')
        // 确保 null/undefined 转换为空字符串
        let value = setting.value ?? ''
        if (value === 'true') value = true
        else if (value === 'false') value = false
        else if (typeof value === 'string' && /^\d+$/.test(value)) value = parseInt(value)
        if (key in settings[group.category]) {
          settings[group.category][key] = value
        }
      }
    }
  } catch (error) {
    console.error(error)
  }
}

const handleLogoError = (e) => {
  e.target.style.display = 'none'
}

const handleLogoDarkError = (e) => {
  e.target.style.display = 'none'
}

const handleFaviconError = (e) => {
  e.target.style.display = 'none'
}

const handleViolationImageError = (e) => {
  e.target.style.display = 'none'
}

const sendTestEmail = async () => {
  if (!testEmail.value) {
    ElMessage.warning(t('admin.testEmailHint'))
    return
  }
  testingEmail.value = true
  try {
    const response = await api.post('/admin/settings/email/test', { to_email: testEmail.value })
    ElMessage.success(response.data.message || t('common.success'))
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('error.submitFailed'))
  } finally {
    testingEmail.value = false
  }
}

const openTemplateEditor = (type) => {
  editingTemplate.value = type
}

const closeTemplateEditor = () => {
  editingTemplate.value = null
}

const resetTemplate = (type) => {
  const defaults = {
    verify: {
      subject: '[{{site_name}}] 验证您的邮箱',
      body: `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><h2 style="color: #2c3e50;">欢迎加入 {{site_name}}！</h2><p>您好，{{username}}！</p><p>感谢您的注册。请点击下方按钮验证您的邮箱地址：</p><div style="text-align: center; margin: 30px 0;"><a href="{{verify_url}}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">验证邮箱</a></div><p>或者复制以下链接到浏览器：</p><p style="background: #f5f5f5; padding: 10px; word-break: break-all;">{{verify_url}}</p><p style="color: #7f8c8d; font-size: 12px;">此链接将在24小时后失效。如果您没有注册账号，请忽略此邮件。</p><hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;"><p style="color: #95a5a6; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p></div></body></html>`
    },
    reset: {
      subject: '[{{site_name}}] 重置密码',
      body: `<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><h2 style="color: #2c3e50;">重置密码</h2><p>您好，{{username}}！</p><p>我们收到了重置您账号密码的请求。请点击下方按钮重置密码：</p><div style="text-align: center; margin: 30px 0;"><a href="{{reset_url}}" style="background-color: #e74c3c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">重置密码</a></div><p>或者复制以下链接到浏览器：</p><p style="background: #f5f5f5; padding: 10px; word-break: break-all;">{{reset_url}}</p><p style="color: #7f8c8d; font-size: 12px;">此链接将在1小时后失效。如果您没有请求重置密码，请忽略此邮件。</p><hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;"><p style="color: #95a5a6; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p></div></body></html>`
    }
  }
  settings.email[`template_${type}_subject`] = defaults[type].subject
  settings.email[`template_${type}_body`] = defaults[type].body
  ElMessage.success(t('common.success'))
}

const saveSettings = async () => {
  saving.value = true
  try {
    const payload = {}
    for (const [category, categorySettings] of Object.entries(settings)) {
      for (const [key, value] of Object.entries(categorySettings)) {
        payload[`${category}_${key}`] = String(value)
      }
    }
    await api.post('/admin/settings/batch', payload)
    ElMessage.success(t('settings.saveSuccess'))
  } catch (error) {
    console.error(error)
    ElMessage.error(t('error.saveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
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

.settings-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
}

// Sidebar Navigation
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

// Settings Content
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
}

// Form Styles
.form-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
  align-items: start;
  margin-bottom: 20px;
  
  &:last-child { margin-bottom: 0; }
  
  &--switch {
    align-items: center;
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

.label-hint {
  font-size: 12px;
  color: var(--text-tertiary);
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
  
  &::placeholder { color: var(--text-tertiary); }
  &:focus { outline: none; border-color: var(--border-medium); background: var(--bg-card); }
  &:disabled { opacity: 0.6; }
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
  cursor: pointer;
}

.form-divider {
  height: 1px;
  background: var(--border-light);
  margin: 24px 0;
}

.form-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 16px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-row--inline {
  display: flex;
  gap: 16px;
  
  .form-col {
    flex: 1;
    min-width: 0;
  }
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .form-input { flex: 1; max-width: 200px; }
  
  &__suffix {
    font-size: 13px;
    color: var(--text-tertiary);
    white-space: nowrap;
  }
}

.logo-input-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .form-input {
    width: 100%;
  }
}

.logo-preview {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  
  img {
    max-width: 200px;
    max-height: 60px;
    object-fit: contain;
  }
  
  &--dark {
    background: #1a1a1a;
  }
}

.favicon-preview {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  
  img {
    width: 32px;
    height: 32px;
    object-fit: contain;
  }
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
  font-size: 12px;
  color: var(--text-muted);
  margin: -12px 0 16px;
}

.slider-input {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .slider {
    flex: 1;
    max-width: 300px;
    height: 6px;
    appearance: none;
    background: var(--bg-tertiary);
    border-radius: 3px;
    
    &::-webkit-slider-thumb {
      appearance: none;
      width: 18px;
      height: 18px;
      background: var(--accent-primary);
      border-radius: 50%;
      cursor: pointer;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
  }
  
  .slider-value {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    min-width: 48px;
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
      &::before { transform: translateX(20px); }
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

// Radio Group
.radio-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  input { display: none; }
  
  &:hover { background: var(--bg-tertiary); }
  
  &.is-active {
    border-color: var(--accent-primary);
    background: var(--bg-card);
  }
  
  &__icon {
    display: flex;
    color: var(--text-tertiary);
  }
  
  &__text {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
  }
}

// Config Section
.config-section {
  margin-top: 8px;
}

.config-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 16px;
}

// Actions
.settings-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-light);
}

.save-hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
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
  
  &--lg {
    padding: 14px 28px;
    font-size: 15px;
  }
}

.btn-loader {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.btn--secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  &:hover { background: var(--bg-tertiary); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

.btn--text {
  background: transparent;
  color: var(--accent-primary);
  padding: 6px 12px;
  &:hover { background: var(--bg-secondary); }
}

.btn--sm {
  padding: 6px 12px;
  font-size: 13px;
}

// Email Settings
.test-email-group {
  display: flex;
  gap: 12px;
  
  .form-input {
    flex: 1;
  }
  
  .btn {
    flex-shrink: 0;
  }
}

.template-hint {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: -8px 0 16px;
  
  code {
    background: var(--bg-secondary);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
    margin: 0 2px;
  }
}

.template-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.template-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  &__title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  &__actions {
    display: flex;
    gap: 4px;
  }
  
  &__preview {
    display: flex;
    gap: 8px;
    font-size: 13px;
  }
  
  .preview-label {
    color: var(--text-tertiary);
    flex-shrink: 0;
  }
  
  .preview-value {
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

// Modal
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  line-height: 1;
  
  &:hover {
    color: var(--text-primary);
  }
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.template-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  min-height: 300px;
}

.variable-hints {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--text-tertiary);
  
  .hint-title {
    font-weight: 600;
    margin-right: 8px;
  }
  
  code {
    background: var(--bg-tertiary);
    padding: 2px 6px;
    border-radius: 4px;
    margin: 0 4px;
    color: var(--text-secondary);
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
  
  .radio-group {
    grid-template-columns: 1fr;
  }
  
  .template-cards {
    grid-template-columns: 1fr;
  }
  
  .test-email-group {
    flex-direction: column;
  }
  
  .modal-content {
    max-height: 80vh;
  }
}
</style>
