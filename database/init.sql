-- ============================================
-- Forimage Image Hosting System
-- MySQL Database Initialization Script
-- ============================================

-- Create database
CREATE DATABASE IF NOT EXISTS `imgbed` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `imgbed`;

-- ============================================
-- Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `hashed_password` VARCHAR(255) NOT NULL,
    `role` ENUM('guest', 'user', 'admin') NOT NULL DEFAULT 'user',
    `status` ENUM('pending', 'active', 'disabled') NOT NULL DEFAULT 'pending',
    
    -- Email verification
    `email_verified` TINYINT(1) NOT NULL DEFAULT 0,
    `email_verify_token` VARCHAR(255) NULL,
    `email_verify_token_expires` DATETIME NULL,
    
    -- Password reset
    `password_reset_token` VARCHAR(255) NULL,
    `password_reset_token_expires` DATETIME NULL,
    
    -- Security
    `failed_login_attempts` INT NOT NULL DEFAULT 0,
    `locked_until` DATETIME NULL,
    `last_login_at` DATETIME NULL,
    `last_login_ip` VARCHAR(45) NULL,
    
    -- Timestamps
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_users_username` (`username`),
    UNIQUE KEY `uk_users_email` (`email`),
    KEY `idx_users_status` (`status`),
    KEY `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Albums Table
-- ============================================
CREATE TABLE IF NOT EXISTS `albums` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(500) NULL,
    `user_id` INT NOT NULL,
    `is_public` TINYINT(1) NOT NULL DEFAULT 0,
    
    -- Timestamps
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_albums_user_id` (`user_id`),
    CONSTRAINT `fk_albums_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Images Table
-- ============================================
CREATE TABLE IF NOT EXISTS `images` (
    `id` INT NOT NULL AUTO_INCREMENT,
    
    -- File info
    `filename` VARCHAR(8) NOT NULL COMMENT '8-char random string',
    `original_filename` VARCHAR(255) NOT NULL,
    `title` VARCHAR(200) NULL COMMENT 'User-editable title',
    `extension` VARCHAR(10) NOT NULL,
    `mime_type` VARCHAR(50) NOT NULL,
    `file_size` BIGINT NOT NULL COMMENT 'In bytes',
    `file_path` VARCHAR(500) NOT NULL COMMENT 'Storage path',
    
    -- Image dimensions
    `width` INT NULL,
    `height` INT NULL,
    
    -- Storage info
    `storage_type` VARCHAR(20) NOT NULL DEFAULT 'local' COMMENT 'local, oss, r2, s3',
    `storage_url` VARCHAR(500) NULL COMMENT 'CDN/Cloud URL if applicable',
    
    -- Ownership
    `user_id` INT NULL COMMENT 'NULL for guest uploads',
    `album_id` INT NULL,
    `guest_ip` VARCHAR(45) NULL COMMENT 'Legacy: For guest uploads only',
    `upload_ip` VARCHAR(45) NULL COMMENT 'IP address of uploader (both guest and user)',
    
    -- Status
    `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'approved',
    `audit_result` TEXT NULL COMMENT 'Audit API response (JSON)',
    
    -- Stats
    `view_count` INT NOT NULL DEFAULT 0,
    
    -- Timestamps
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_images_filename` (`filename`),
    KEY `idx_images_user_id` (`user_id`),
    KEY `idx_images_album_id` (`album_id`),
    KEY `idx_images_status` (`status`),
    KEY `idx_images_created_at` (`created_at`),
    CONSTRAINT `fk_images_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_images_album` FOREIGN KEY (`album_id`) REFERENCES `albums` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- System Settings Table
-- ============================================
CREATE TABLE IF NOT EXISTS `system_settings` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL,
    `value` TEXT NULL,
    `description` VARCHAR(500) NULL,
    `category` VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT 'general, upload, storage, security, audit',
    
    -- Timestamps
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_settings_key` (`key`),
    KEY `idx_settings_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Blacklist Table (IP/User ban)
-- ============================================
CREATE TABLE IF NOT EXISTS `blacklist` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ip_address` VARCHAR(45) NULL COMMENT 'Banned IP address',
    `user_id` INT NULL COMMENT 'Banned user ID',
    `reason` VARCHAR(500) NOT NULL COMMENT 'Ban reason',
    `ban_type` ENUM('TEMPORARY', 'PERMANENT') NOT NULL DEFAULT 'TEMPORARY',
    `expires_at` DATETIME NULL COMMENT 'NULL for permanent ban',
    `violation_count` INT NOT NULL DEFAULT 1 COMMENT 'Total violation count',
    `created_by` INT NULL COMMENT 'Admin who created the ban',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Lift tracking (preserves history instead of deleting)
    `lifted_at` DATETIME NULL COMMENT 'When the ban was lifted',
    `lifted_by` INT NULL COMMENT 'Admin who lifted the ban',
    `lift_reason` VARCHAR(500) NULL COMMENT 'Reason for lifting',
    
    PRIMARY KEY (`id`),
    KEY `idx_blacklist_ip` (`ip_address`),
    KEY `idx_blacklist_user_id` (`user_id`),
    KEY `idx_blacklist_expires` (`expires_at`),
    KEY `idx_blacklist_lifted` (`lifted_at`),
    CONSTRAINT `fk_blacklist_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_blacklist_admin` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_blacklist_lifter` FOREIGN KEY (`lifted_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Violation Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS `violation_logs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ip_address` VARCHAR(45) NOT NULL,
    `user_id` INT NULL,
    `image_id` INT NULL,
    `violation_type` VARCHAR(50) NOT NULL COMMENT 'audit_failed, rate_limit_exceeded, etc.',
    `details` TEXT NULL COMMENT 'JSON with details',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_violation_ip` (`ip_address`),
    KEY `idx_violation_user` (`user_id`),
    KEY `idx_violation_type` (`violation_type`),
    KEY `idx_violation_created` (`created_at`),
    CONSTRAINT `fk_violation_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_violation_image` FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Ban Appeals Table
-- ============================================
CREATE TABLE IF NOT EXISTS `ban_appeals` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `blacklist_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `reason` TEXT NOT NULL COMMENT 'Appeal reason from user',
    `status` ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    `admin_response` TEXT NULL,
    `handled_by` INT NULL,
    `handled_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_appeals_blacklist` (`blacklist_id`),
    KEY `idx_appeals_user` (`user_id`),
    KEY `idx_appeals_status` (`status`),
    CONSTRAINT `fk_appeals_blacklist` FOREIGN KEY (`blacklist_id`) REFERENCES `blacklist` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_appeals_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_appeals_admin` FOREIGN KEY (`handled_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Audit Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    
    -- Action info
    `action` VARCHAR(50) NOT NULL COMMENT 'login, upload, delete, admin_action, etc.',
    `resource_type` VARCHAR(50) NULL COMMENT 'user, image, album, settings',
    `resource_id` INT NULL,
    
    -- Actor info
    `user_id` INT NULL,
    `ip_address` VARCHAR(45) NOT NULL,
    `user_agent` VARCHAR(500) NULL,
    
    -- Details
    `details` TEXT NULL COMMENT 'JSON string with additional info',
    `status` VARCHAR(20) NOT NULL DEFAULT 'success' COMMENT 'success, failure',
    
    -- Timestamps
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_audit_user_id` (`user_id`),
    KEY `idx_audit_action` (`action`),
    KEY `idx_audit_created_at` (`created_at`),
    CONSTRAINT `fk_audit_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Performance Indexes
-- 复合索引优化查询性能
-- ============================================

-- 图片查询优化：用户+状态+时间
CREATE INDEX IF NOT EXISTS `idx_images_user_status_created` ON `images` (`user_id`, `status`, `created_at` DESC);

-- 图片查询优化：相册+时间
CREATE INDEX IF NOT EXISTS `idx_images_album_created` ON `images` (`album_id`, `created_at` DESC);

-- 审计日志查询优化：时间+操作类型
CREATE INDEX IF NOT EXISTS `idx_audit_created_action` ON `audit_logs` (`created_at` DESC, `action`);

-- 违规记录查询优化：时间+类型
CREATE INDEX IF NOT EXISTS `idx_violation_created_type` ON `violation_logs` (`created_at` DESC, `violation_type`);

-- 封禁列表查询优化：活跃状态
CREATE INDEX IF NOT EXISTS `idx_blacklist_active` ON `blacklist` (`lifted_at`, `expires_at`);

-- ============================================
-- Default System Settings
-- 使用独立 INSERT 语句，避免批量插入失败
-- ============================================

-- General Settings
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_name', 'Forimage', '站点名称（导航栏显示）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_title', 'Forimage - 简洁优雅的图床服务', '站点标题（SEO用，显示在浏览器标签）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_description', '免费稳定的图片托管服务，支持多格式上传，全球CDN加速', 'SEO描述（meta description）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_slogan', '简洁优雅的图床服务', '首页宣传语（显示在Logo下方）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_footer', 'Forimage - 让图片分享更简单', '页脚文字', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_url', 'http://localhost:3000', '站点URL', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_logo', '', '站点Logo URL（留空显示文字）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_site_favicon', '', '站点Favicon URL（留空使用默认）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_timezone', 'Asia/Shanghai', '系统时区（如 Asia/Shanghai, UTC）', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_enable_registration', 'true', '是否允许注册', 'general');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('general_enable_guest_upload', 'true', '是否允许游客上传', 'general');

-- Upload Settings
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('upload_max_size_guest', '5242880', '游客最大上传大小（字节）', 'upload');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('upload_max_size_user', '10485760', '会员最大上传大小（字节）', 'upload');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('upload_allowed_extensions', 'png,jpg,jpeg,gif,webp', '允许的文件扩展名', 'upload');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('upload_compression_quality', '85', '图片压缩质量（1-100）', 'upload');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('upload_max_dimension', '', '最大图片尺寸（空为不限制）', 'upload');

-- Security / Rate Limiting
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_guest_per_minute', '3', '游客每分钟上传限制', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_user_per_minute', '10', '会员每分钟上传限制', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_guest_per_hour', '10', '游客每小时上传限制', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_user_per_hour', '100', '会员每小时上传限制', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_guest_per_day', '30', '游客每天上传限制', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_user_per_day', '500', '会员每天上传限制', 'security');

-- Security / Auto Ban
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_auto_ban_enabled', 'true', '是否启用自动封禁', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_audit_fail_threshold', '3', '审核失败自动封禁阈值', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_exceed_threshold', '3', '超速封禁阈值', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_temp_ban_duration', '1440', '临时封禁时长（分钟）', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_rate_limit_login_attempts', '5', '登录失败锁定次数', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_real_ip_header', 'X-Forwarded-For', '真实IP获取头', 'security');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('security_trust_proxy', 'true', '是否信任代理头获取真实IP', 'security');

-- Storage Settings
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_type', 'local', '存储类型 (local/s3c/oss/cos)', 'storage');
-- S3 Compatible Storage (unified)
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_provider', 'custom', 'S3兼容存储提供商', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_access_key_id', '', 'S3兼容存储 Access Key ID', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_secret_access_key', '', 'S3兼容存储 Secret Access Key', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_bucket_name', '', 'S3兼容存储 Bucket名称', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_endpoint_url', '', 'S3兼容存储 Endpoint URL', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_region', '', 'S3兼容存储 Region', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_s3c_public_url', '', 'S3兼容存储 公开访问URL', 'storage');
-- Aliyun OSS (native SDK)
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_oss_access_key_id', '', '阿里云OSS Access Key ID', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_oss_access_key_secret', '', '阿里云OSS Access Key Secret', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_oss_bucket_name', '', '阿里云OSS Bucket名称', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_oss_endpoint', '', '阿里云OSS Endpoint', 'storage');
-- Tencent COS (native SDK)
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_cos_secret_id', '', '腾讯云COS SecretId', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_cos_secret_key', '', '腾讯云COS SecretKey', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_cos_bucket_name', '', '腾讯云COS Bucket名称', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_cos_region', '', '腾讯云COS Region', 'storage');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('storage_cos_public_url', '', '腾讯云COS 公开访问URL', 'storage');

-- Audit Settings
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('audit_enabled', 'false', '是否启用内容审核', 'audit');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('audit_provider', '', '审核服务提供商', 'audit');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('audit_api_key', '', '审核API Key', 'audit');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('audit_api_secret', '', '审核API Secret', 'audit');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('audit_auto_reject', 'false', '自动拒绝违规图片', 'audit');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('audit_violation_image', '', '违规图片替换图URL（留空则返回403错误）', 'audit');

-- Email Settings
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_enabled', 'false', '是否启用邮件功能', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_smtp_host', '', 'SMTP服务器地址', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_smtp_port', '587', 'SMTP端口', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_smtp_user', '', 'SMTP用户名', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_smtp_password', '', 'SMTP密码', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_smtp_ssl', 'false', '使用SSL连接', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_from_address', '', '发件人邮箱地址', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_from_name', 'Forimage', '发件人名称', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_template_verify_subject', '[{{site_name}}] 验证您的邮箱', '邮箱验证邮件主题', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_template_verify_body', '<!DOCTYPE html><html><head><meta charset=\"UTF-8\"></head><body style=\"font-family: Arial, sans-serif; line-height: 1.6; color: #333;\"><div style=\"max-width: 600px; margin: 0 auto; padding: 20px;\"><h2 style=\"color: #2c3e50;\">欢迎加入 {{site_name}}！</h2><p>您好，{{username}}！</p><p>感谢您的注册。请点击下方按钮验证您的邮箱地址：</p><div style=\"text-align: center; margin: 30px 0;\"><a href=\"{{verify_url}}\" style=\"background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;\">验证邮箱</a></div><p>或者复制以下链接到浏览器：</p><p style=\"background: #f5f5f5; padding: 10px; word-break: break-all;\">{{verify_url}}</p><p style=\"color: #7f8c8d; font-size: 12px;\">此链接将在24小时后失效。如果您没有注册账号，请忽略此邮件。</p><hr style=\"border: none; border-top: 1px solid #eee; margin: 20px 0;\"><p style=\"color: #95a5a6; font-size: 12px;\">此邮件由系统自动发送，请勿回复。</p></div></body></html>', '邮箱验证邮件模板', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_template_reset_subject', '[{{site_name}}] 重置密码', '密码重置邮件主题', 'email');
INSERT INTO `system_settings` (`key`, `value`, `description`, `category`) VALUES ('email_template_reset_body', '<!DOCTYPE html><html><head><meta charset=\"UTF-8\"></head><body style=\"font-family: Arial, sans-serif; line-height: 1.6; color: #333;\"><div style=\"max-width: 600px; margin: 0 auto; padding: 20px;\"><h2 style=\"color: #2c3e50;\">重置密码</h2><p>您好，{{username}}！</p><p>我们收到了重置您账号密码的请求。请点击下方按钮重置密码：</p><div style=\"text-align: center; margin: 30px 0;\"><a href=\"{{reset_url}}\" style=\"background-color: #e74c3c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;\">重置密码</a></div><p>或者复制以下链接到浏览器：</p><p style=\"background: #f5f5f5; padding: 10px; word-break: break-all;\">{{reset_url}}</p><p style=\"color: #7f8c8d; font-size: 12px;\">此链接将在1小时后失效。如果您没有请求重置密码，请忽略此邮件。</p><hr style=\"border: none; border-top: 1px solid #eee; margin: 20px 0;\"><p style=\"color: #95a5a6; font-size: 12px;\">此邮件由系统自动发送，请勿回复。</p></div></body></html>', '密码重置邮件模板', 'email');

-- ============================================
-- Create Default Admin User
-- Password: Admin123 (首次登录后请立即修改!)
-- ============================================
INSERT INTO `users` (`username`, `email`, `hashed_password`, `role`, `status`, `email_verified`) VALUES ('admin', 'admin@example.com', '$2b$12$8WOZ7YRCuD636x5DlH7vLON2JVtEDaGnBZpfuQeJdBGNrO208BtI2', 'admin', 'active', 1);

-- ============================================
-- 数据验证查询（导入后请执行以下查询验证）
-- ============================================
-- SELECT COUNT(*) AS settings_count FROM system_settings;  -- 应该是 54（含邮件设置12条）
-- SELECT COUNT(*) AS users_count FROM users;               -- 应该是 1
-- SELECT username, role, status FROM users WHERE username = 'admin';


-- ============================================
-- Backup Nodes Table (Multi-Node Backup)
-- ============================================
CREATE TABLE IF NOT EXISTS `backup_nodes` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL COMMENT '节点名称',
    `protocol` ENUM('ftp', 'sftp', 's3', 'webdav') NOT NULL,
    `is_enabled` TINYINT(1) NOT NULL DEFAULT 1,
    
    -- Connection settings (encrypted JSON)
    `connection_config` TEXT NOT NULL COMMENT '加密的连接配置JSON',
    
    -- Sync strategy
    `sync_strategy` ENUM('realtime', 'scheduled', 'manual') NOT NULL DEFAULT 'manual',
    `schedule_cron` VARCHAR(100) NULL COMMENT 'Cron表达式（scheduled模式）',
    `file_types` VARCHAR(50) DEFAULT 'original' COMMENT 'original,thumbnail,both',
    
    -- Performance limits
    `max_bandwidth` INT NULL COMMENT '最大带宽(KB/s)，NULL为不限制',
    `max_concurrent` INT DEFAULT 3 COMMENT '最大并发数',
    
    -- Status
    `last_sync_at` DATETIME NULL,
    `last_sync_status` ENUM('success', 'partial', 'failed') NULL,
    `total_files` INT DEFAULT 0,
    `total_bytes` BIGINT DEFAULT 0,
    
    -- Timestamps
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_backup_nodes_protocol` (`protocol`),
    KEY `idx_backup_nodes_enabled` (`is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Backup File Status Table
-- ============================================
CREATE TABLE IF NOT EXISTS `backup_file_status` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `node_id` INT NOT NULL,
    `image_id` INT NOT NULL,
    `remote_path` VARCHAR(500) NOT NULL,
    `file_size` BIGINT NOT NULL,
    `checksum` VARCHAR(64) NULL COMMENT 'MD5 or SHA256',
    `status` ENUM('pending', 'synced', 'failed', 'deleted') NOT NULL DEFAULT 'pending',
    `last_sync_at` DATETIME NULL,
    `error_message` VARCHAR(500) NULL,
    `retry_count` INT DEFAULT 0,
    
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_node_image` (`node_id`, `image_id`),
    KEY `idx_backup_status_node` (`node_id`),
    KEY `idx_backup_status_status` (`status`),
    CONSTRAINT `fk_backup_status_node` FOREIGN KEY (`node_id`) REFERENCES `backup_nodes` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_backup_status_image` FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Backup Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS `backup_logs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `node_id` INT NOT NULL,
    `task_type` ENUM('backup', 'realtime', 'restore', 'sync', 'test') NOT NULL,
    `status` ENUM('running', 'success', 'partial', 'failed', 'cancelled') NOT NULL,
    
    -- Statistics
    `files_total` INT DEFAULT 0,
    `files_success` INT DEFAULT 0,
    `files_failed` INT DEFAULT 0,
    `bytes_transferred` BIGINT DEFAULT 0,
    
    -- Timing
    `started_at` DATETIME NOT NULL,
    `completed_at` DATETIME NULL,
    `duration_seconds` INT NULL,
    
    -- Details
    `error_details` TEXT NULL COMMENT 'JSON array of errors',
    `triggered_by` INT NULL COMMENT 'Admin user ID',
    
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    KEY `idx_backup_logs_node` (`node_id`),
    KEY `idx_backup_logs_status` (`status`),
    KEY `idx_backup_logs_created` (`created_at`),
    CONSTRAINT `fk_backup_logs_node` FOREIGN KEY (`node_id`) REFERENCES `backup_nodes` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_backup_logs_user` FOREIGN KEY (`triggered_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
