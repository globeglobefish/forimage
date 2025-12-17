from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.settings import SystemSettings
from app.api.deps import get_admin_user
import json

router = APIRouter(prefix="/settings")


class SettingResponse(BaseModel):
    key: str
    value: Optional[str]
    description: Optional[str]
    category: str


class SettingUpdate(BaseModel):
    value: str


class SettingsGroupResponse(BaseModel):
    category: str
    settings: List[SettingResponse]


# Default settings definitions
DEFAULT_SETTINGS = {
    "upload": {
        "max_size_guest": {"value": "5242880", "description": "Maximum upload size for guests (bytes)"},
        "max_size_user": {"value": "10485760", "description": "Maximum upload size for users (bytes)"},
        "allowed_extensions": {"value": "png,jpg,jpeg,gif,webp", "description": "Allowed file extensions"},
        "compression_quality": {"value": "85", "description": "Image compression quality (1-100)"},
        "max_dimension": {"value": "", "description": "Maximum image dimension (empty for no limit)"},
    },
    "storage": {
        "type": {"value": "local", "description": "Storage type: local, s3c, oss, cos"},
        # Local storage
        "local_public_url": {"value": "", "description": "本地存储自定义CDN域名"},
        # S3-Compatible Storage (unified)
        "s3c_provider": {"value": "custom", "description": "S3兼容存储提供商: aws, r2, cos, minio, b2, spaces, custom"},
        "s3c_access_key_id": {"value": "", "description": "S3兼容存储 Access Key ID"},
        "s3c_secret_access_key": {"value": "", "description": "S3兼容存储 Secret Access Key"},
        "s3c_bucket_name": {"value": "", "description": "S3兼容存储 Bucket名称"},
        "s3c_endpoint_url": {"value": "", "description": "S3兼容存储 Endpoint URL（AWS S3可留空）"},
        "s3c_region": {"value": "", "description": "S3兼容存储 Region（R2填auto）"},
        "s3c_public_url": {"value": "", "description": "S3兼容存储 自定义公开访问URL"},
        # Aliyun OSS (native SDK)
        "oss_access_key_id": {"value": "", "description": "阿里云OSS Access Key ID"},
        "oss_access_key_secret": {"value": "", "description": "阿里云OSS Access Key Secret"},
        "oss_bucket_name": {"value": "", "description": "阿里云OSS Bucket名称"},
        "oss_endpoint": {"value": "", "description": "阿里云OSS Endpoint"},
        # Tencent Cloud COS (native SDK)
        "cos_secret_id": {"value": "", "description": "腾讯云COS SecretId"},
        "cos_secret_key": {"value": "", "description": "腾讯云COS SecretKey"},
        "cos_bucket_name": {"value": "", "description": "腾讯云COS Bucket名称（格式：bucket-appid）"},
        "cos_region": {"value": "", "description": "腾讯云COS Region（如ap-guangzhou）"},
        "cos_public_url": {"value": "", "description": "腾讯云COS 自定义域名"},
    },
    "security": {
        "rate_limit_guest_per_minute": {"value": "3", "description": "Guest upload limit per minute"},
        "rate_limit_guest_per_hour": {"value": "10", "description": "Guest upload limit per hour"},
        "rate_limit_guest_per_day": {"value": "30", "description": "Guest upload limit per day"},
        "rate_limit_user_per_minute": {"value": "10", "description": "User upload limit per minute"},
        "rate_limit_user_per_hour": {"value": "100", "description": "User upload limit per hour"},
        "rate_limit_user_per_day": {"value": "500", "description": "User upload limit per day"},
        "rate_limit_login_attempts": {"value": "5", "description": "Max login attempts before lockout"},
        "auto_ban_enabled": {"value": "true", "description": "Enable automatic banning"},
        "audit_fail_threshold": {"value": "3", "description": "Auto ban after N audit failures"},
        "rate_exceed_threshold": {"value": "3", "description": "Auto ban after N rate limit violations"},
        "temp_ban_duration": {"value": "1440", "description": "Temporary ban duration in minutes"},
        "real_ip_header": {"value": "X-Forwarded-For", "description": "Header for real IP (X-Forwarded-For, X-Real-IP, CF-Connecting-IP)"},
        "trust_proxy": {"value": "true", "description": "Trust proxy headers for real IP"},
    },
    "audit": {
        "enabled": {"value": "false", "description": "Enable image content moderation"},
        "provider": {"value": "", "description": "Audit provider: aliyun, tencent"},
        "api_key": {"value": "", "description": "Audit API Key"},
        "api_secret": {"value": "", "description": "Audit API Secret"},
        "auto_reject": {"value": "false", "description": "Auto reject flagged images"},
        "violation_image": {"value": "", "description": "违规图片替换图URL（留空则返回403错误）"},
        "tencent_bucket": {"value": "", "description": "腾讯云COS Bucket名称（格式：bucket-appid）"},
        "tencent_region": {"value": "", "description": "腾讯云COS Region（如ap-guangzhou）"},
    },
    "email": {
        "enabled": {"value": "false", "description": "是否启用邮件功能"},
        "smtp_host": {"value": "", "description": "SMTP服务器地址"},
        "smtp_port": {"value": "587", "description": "SMTP端口"},
        "smtp_user": {"value": "", "description": "SMTP用户名"},
        "smtp_password": {"value": "", "description": "SMTP密码"},
        "smtp_ssl": {"value": "false", "description": "使用SSL连接"},
        "from_address": {"value": "", "description": "发件人邮箱地址"},
        "from_name": {"value": "Forimage", "description": "发件人名称"},
        "template_verify_subject": {"value": "[{{site_name}}] 验证您的邮箱", "description": "邮箱验证邮件主题"},
        "template_verify_body": {"value": """<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><h2 style="color: #2c3e50;">欢迎加入 {{site_name}}！</h2><p>您好，{{username}}！</p><p>感谢您的注册。请点击下方按钮验证您的邮箱地址：</p><div style="text-align: center; margin: 30px 0;"><a href="{{verify_url}}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">验证邮箱</a></div><p>或者复制以下链接到浏览器：</p><p style="background: #f5f5f5; padding: 10px; word-break: break-all;">{{verify_url}}</p><p style="color: #7f8c8d; font-size: 12px;">此链接将在24小时后失效。如果您没有注册账号，请忽略此邮件。</p><hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;"><p style="color: #95a5a6; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p></div></body></html>""", "description": "邮箱验证邮件模板"},
        "template_reset_subject": {"value": "[{{site_name}}] 重置密码", "description": "密码重置邮件主题"},
        "template_reset_body": {"value": """<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;"><div style="max-width: 600px; margin: 0 auto; padding: 20px;"><h2 style="color: #2c3e50;">重置密码</h2><p>您好，{{username}}！</p><p>我们收到了重置您账号密码的请求。请点击下方按钮重置密码：</p><div style="text-align: center; margin: 30px 0;"><a href="{{reset_url}}" style="background-color: #e74c3c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">重置密码</a></div><p>或者复制以下链接到浏览器：</p><p style="background: #f5f5f5; padding: 10px; word-break: break-all;">{{reset_url}}</p><p style="color: #7f8c8d; font-size: 12px;">此链接将在1小时后失效。如果您没有请求重置密码，请忽略此邮件。</p><hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;"><p style="color: #95a5a6; font-size: 12px;">此邮件由系统自动发送，请勿回复。</p></div></body></html>""", "description": "密码重置邮件模板"},
    },
    "general": {
        "site_name": {"value": "Forimage", "description": "站点名称（导航栏显示）"},
        "site_title": {"value": "Forimage - 简洁优雅的图床服务", "description": "站点标题（SEO用，浏览器标签）"},
        "site_description": {"value": "免费稳定的图片托管服务，支持多格式上传，全球CDN加速", "description": "SEO描述（meta description）"},
        "site_slogan": {"value": "简洁优雅的图床服务", "description": "首页宣传语（显示在Logo下方）"},
        "site_footer": {"value": "Forimage - 让图片分享更简单", "description": "页脚文字"},
        "site_url": {"value": "http://localhost:3000", "description": "站点URL"},
        "site_logo": {"value": "", "description": "站点Logo URL（留空显示文字）"},
        "site_logo_dark": {"value": "", "description": "深色模式Logo URL（留空使用浅色Logo）"},
        "site_favicon": {"value": "", "description": "站点Favicon URL（留空使用默认）"},
        "timezone": {"value": "Asia/Shanghai", "description": "系统时区（如 Asia/Shanghai, UTC）"},
        "enable_registration": {"value": "true", "description": "是否允许注册"},
        "enable_guest_upload": {"value": "true", "description": "是否允许游客上传"},
    },
}


async def get_or_create_setting(db: AsyncSession, key: str, category: str) -> SystemSettings:
    """Get setting from database or create with default value."""
    result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        # Create with default value
        default = DEFAULT_SETTINGS.get(category, {}).get(key.split("_", 1)[-1] if "_" in key else key, {})
        setting = SystemSettings(
            key=key,
            value=default.get("value", ""),
            description=default.get("description", ""),
            category=category,
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
    
    return setting


@router.get("", response_model=List[SettingsGroupResponse])
async def get_all_settings(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all settings grouped by category."""
    result = await db.execute(select(SystemSettings).order_by(SystemSettings.category))
    db_settings = {s.key: s for s in result.scalars().all()}
    
    groups = []
    for category, settings_def in DEFAULT_SETTINGS.items():
        settings_list = []
        for key_suffix, default in settings_def.items():
            full_key = f"{category}_{key_suffix}"
            if full_key in db_settings:
                setting = db_settings[full_key]
            else:
                setting = SystemSettings(
                    key=full_key,
                    value=default["value"],
                    description=default["description"],
                    category=category,
                )
            settings_list.append(SettingResponse(
                key=full_key,
                value=setting.value if setting.value is not None else "",
                description=setting.description,
                category=category,
            ))
        
        groups.append(SettingsGroupResponse(
            category=category,
            settings=settings_list,
        ))
    
    return groups


@router.get("/{category}", response_model=SettingsGroupResponse)
async def get_settings_by_category(
    category: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get settings for a specific category."""
    import logging
    logger = logging.getLogger(__name__)
    
    if category not in DEFAULT_SETTINGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.category == category)
    )
    db_settings = {s.key: s for s in result.scalars().all()}
    logger.info(f"Get settings for category '{category}': found {len(db_settings)} in database")
    
    settings_list = []
    for key_suffix, default in DEFAULT_SETTINGS[category].items():
        full_key = f"{category}_{key_suffix}"
        if full_key in db_settings:
            setting = db_settings[full_key]
            logger.info(f"Using DB value for {full_key}: '{setting.value}'")
        else:
            logger.warning(f"No DB entry for {full_key}, using default: '{default['value']}'")
            setting = SystemSettings(
                key=full_key,
                value=default["value"],
                description=default["description"],
                category=category,
            )
        settings_list.append(SettingResponse(
            key=full_key,
            value=setting.value if setting.value is not None else "",
            description=setting.description,
            category=category,
        ))
    
    return SettingsGroupResponse(
        category=category,
        settings=settings_list,
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    data: SettingUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a setting value."""
    from app.services.settings import invalidate_cache
    
    # Parse category from key
    parts = key.split("_", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid setting key format"
        )
    
    category = parts[0]
    if category not in DEFAULT_SETTINGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid setting category"
        )
    
    # Get or create setting
    result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
    setting = result.scalar_one_or_none()
    
    if not setting:
        key_suffix = parts[1]
        default = DEFAULT_SETTINGS.get(category, {}).get(key_suffix, {})
        setting = SystemSettings(
            key=key,
            value=data.value,
            description=default.get("description", ""),
            category=category,
        )
        db.add(setting)
    else:
        setting.value = data.value
    
    await db.commit()
    await db.refresh(setting)
    
    # Invalidate settings cache so changes take effect immediately
    invalidate_cache()
    
    return SettingResponse(
        key=setting.key,
        value=setting.value,
        description=setting.description,
        category=setting.category,
    )


@router.post("/batch")
async def batch_update_settings(
    settings_data: Dict[str, str],
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update multiple settings at once."""
    from app.services.settings import invalidate_cache
    from app.api.admin.audit import create_audit_log
    from app.utils.rate_limit import get_real_ip
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Batch update settings: received {len(settings_data)} items: {settings_data}")
    
    updated = 0
    created = 0
    
    for key, value in settings_data.items():
        parts = key.split("_", 1)
        if len(parts) != 2:
            logger.warning(f"Skipping invalid key format: {key}")
            continue
        
        category = parts[0]
        if category not in DEFAULT_SETTINGS:
            logger.warning(f"Skipping unknown category: {category} for key: {key}")
            continue
        
        # Query existing setting
        result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
        setting = result.scalar_one_or_none()
        
        if setting:
            old_value = setting.value
            setting.value = str(value)
            setting.category = category
            logger.info(f"UPDATE: {key} from '{old_value}' to '{value}'")
            updated += 1
        else:
            key_suffix = parts[1]
            default = DEFAULT_SETTINGS.get(category, {}).get(key_suffix, {})
            setting = SystemSettings(
                key=key,
                value=str(value),
                description=default.get("description", ""),
                category=category,
            )
            db.add(setting)
            logger.info(f"CREATE: {key} = '{value}'")
            created += 1
    
    try:
        await db.commit()
        logger.info(f"Batch update SUCCESS: {updated} updated, {created} created")
    except Exception as e:
        logger.error(f"Batch update FAILED: {e}")
        await db.rollback()
        raise
    
    # Invalidate settings cache
    invalidate_cache()
    
    # Refresh IP header settings if security settings were updated
    if any(key.startswith("security_") for key in settings_data.keys()):
        try:
            from app.utils.rate_limit import refresh_ip_header_settings
            await refresh_ip_header_settings()
            logger.info("IP header settings refreshed")
        except Exception as e:
            logger.warning(f"Failed to refresh IP header settings: {e}")
    
    # Verify the save by reading back
    verify_result = await db.execute(select(SystemSettings).where(SystemSettings.category == "security"))
    verify_settings = {s.key: s.value for s in verify_result.scalars().all()}
    logger.info(f"Verification read: {verify_settings}")
    
    # 记录审计日志
    ip = get_real_ip(request)
    await create_audit_log(
        db=db,
        action="admin_settings",
        ip_address=ip,
        user_id=admin.id,
        resource_type="settings",
        resource_id=None,
        user_agent=request.headers.get("User-Agent"),
        details=f"Admin updated {updated + created} settings",
        log_status="success"
    )
    
    return {"message": f"Updated {updated}, created {created} settings", "verified": verify_settings}


class EmailTestRequest(BaseModel):
    to_email: str


@router.post("/email/test")
async def test_email_config(
    data: EmailTestRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Test email configuration by sending a test email."""
    from app.services import settings as settings_service
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if email is enabled
    email_enabled = await settings_service.is_email_enabled()
    if not email_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮件功能未启用，请先启用邮件功能"
        )
    
    # Get SMTP settings
    smtp_host = await settings_service.get_smtp_host()
    smtp_port = await settings_service.get_smtp_port()
    smtp_user = await settings_service.get_smtp_user()
    smtp_password = await settings_service.get_smtp_password()
    smtp_ssl = await settings_service.is_smtp_ssl()
    from_address = await settings_service.get_email_from_address()
    from_name = await settings_service.get_email_from_name()
    site_name = await settings_service.get_site_name()
    
    if not smtp_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP服务器地址未配置"
        )
    
    if not from_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="发件人邮箱地址未配置"
        )
    
    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart("alternative")
        message["From"] = f"{from_name} <{from_address}>"
        message["To"] = data.to_email
        message["Subject"] = f"[{site_name}] 邮件配置测试"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">邮件配置测试成功！</h2>
                <p>恭喜！您的邮件服务配置正确。</p>
                <p>以下是您的配置信息：</p>
                <ul>
                    <li>SMTP服务器：{smtp_host}</li>
                    <li>SMTP端口：{smtp_port}</li>
                    <li>发件人：{from_name} &lt;{from_address}&gt;</li>
                    <li>SSL/TLS：{'是' if smtp_ssl else '否（使用STARTTLS）'}</li>
                </ul>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    此邮件由 {site_name} 系统自动发送。
                </p>
            </div>
        </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, "html"))
        
        # Send email
        if smtp_ssl:
            # Use SSL directly
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user if smtp_user else None,
                password=smtp_password if smtp_password else None,
                use_tls=True,
            )
        else:
            # Use STARTTLS
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user if smtp_user else None,
                password=smtp_password if smtp_password else None,
                start_tls=True,
            )
        
        logger.info(f"Test email sent successfully to {data.to_email}")
        return {"success": True, "message": f"测试邮件已发送至 {data.to_email}"}
        
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMTP认证失败，请检查用户名和密码"
        )
    except aiosmtplib.SMTPConnectError as e:
        logger.error(f"SMTP connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法连接到SMTP服务器 {smtp_host}:{smtp_port}"
        )
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"发送失败：{str(e)}"
        )
