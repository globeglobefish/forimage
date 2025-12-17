"""
Email Service
Sends emails using SMTP configuration from database.
Supports customizable email templates with variable substitution.
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)


def render_template(template: str, variables: dict) -> str:
    """
    Render template with variable substitution.
    Variables are in format {{variable_name}}.
    """
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """Send email using SMTP settings from database."""
    from app.services import settings as settings_service
    
    # Check if email is enabled
    email_enabled = await settings_service.is_email_enabled()
    smtp_host = await settings_service.get_smtp_host()
    
    if not email_enabled or not smtp_host:
        logger.info(f"[DEV MODE] Email to {to_email}")
        logger.info(f"[DEV MODE] Subject: {subject}")
        logger.info(f"[DEV MODE] Content: {text_content or html_content[:200]}...")
        return True
    
    try:
        import aiosmtplib
        
        # Get SMTP settings from database
        smtp_port = await settings_service.get_smtp_port()
        smtp_user = await settings_service.get_smtp_user()
        smtp_password = await settings_service.get_smtp_password()
        smtp_ssl = await settings_service.is_smtp_ssl()
        from_address = await settings_service.get_email_from_address()
        from_name = await settings_service.get_email_from_name()
        
        message = MIMEMultipart("alternative")
        message["From"] = f"{from_name} <{from_address}>"
        message["To"] = to_email
        message["Subject"] = subject

        if text_content:
            message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))

        if smtp_ssl:
            # Use SSL directly (port 465)
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user if smtp_user else None,
                password=smtp_password if smtp_password else None,
                use_tls=True,
            )
        else:
            # Use STARTTLS (port 587)
            await aiosmtplib.send(
                message,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user if smtp_user else None,
                password=smtp_password if smtp_password else None,
                start_tls=True,
            )
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_verification_email(to_email: str, username: str, token: str) -> bool:
    """Send email verification link using template from database."""
    from app.services import settings as settings_service
    
    # Get site settings
    site_name = await settings_service.get_site_name()
    site_url = await settings_service.get_setting("general_site_url", "http://localhost:3000")
    verify_url = f"{site_url}/verify-email?token={token}"
    
    # Get template from database
    subject_template, body_template = await settings_service.get_email_template("verify")
    
    # Prepare variables
    variables = {
        "site_name": site_name,
        "username": username,
        "verify_url": verify_url,
        "token": token,
    }
    
    # Render templates
    subject = render_template(subject_template, variables)
    html_content = render_template(body_template, variables)
    
    # Generate plain text version
    text_content = f"""
欢迎加入 {site_name}！

您好，{username}！

感谢您的注册。请访问以下链接验证您的邮箱地址：
{verify_url}

此链接将在24小时后失效。如果您没有注册账号，请忽略此邮件。
"""
    
    return await send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, username: str, token: str) -> bool:
    """Send password reset link using template from database."""
    from app.services import settings as settings_service
    
    # Get site settings
    site_name = await settings_service.get_site_name()
    site_url = await settings_service.get_setting("general_site_url", "http://localhost:3000")
    reset_url = f"{site_url}/reset-password?token={token}"
    
    # Get template from database
    subject_template, body_template = await settings_service.get_email_template("reset")
    
    # Prepare variables
    variables = {
        "site_name": site_name,
        "username": username,
        "reset_url": reset_url,
        "token": token,
    }
    
    # Render templates
    subject = render_template(subject_template, variables)
    html_content = render_template(body_template, variables)
    
    # Generate plain text version
    text_content = f"""
重置密码

您好，{username}！

我们收到了重置您账号密码的请求。请访问以下链接重置密码：
{reset_url}

此链接将在1小时后失效。如果您没有请求重置密码，请忽略此邮件。
"""
    
    return await send_email(to_email, subject, html_content, text_content)
