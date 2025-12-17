from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import logging
import re
from app.database import get_db
from app.models.user import User, UserStatus, UserRole
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, PasswordReset, PasswordResetConfirm
from app.utils.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    decode_token,
    generate_verification_token
)
from app.utils.rate_limit import (
    get_real_ip, 
    check_login_attempts, 
    record_failed_login, 
    clear_login_attempts,
    check_rate_limit
)
from app.utils.captcha import create_captcha_redis, verify_captcha_redis
from app.services.email import send_verification_email, send_password_reset_email
from app.config import get_settings
from app.api.admin.audit import create_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
logger = logging.getLogger(__name__)

# Regex patterns
USERNAME_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


# Extended schemas with captcha
class UserCreateWithCaptcha(BaseModel):
    username: str
    email: str
    password: str
    captcha_id: str
    captcha_code: str


class PasswordResetWithCaptcha(BaseModel):
    email: str
    captcha_id: str
    captcha_code: str


@router.get("/captcha")
async def get_captcha():
    """Generate a new captcha image."""
    captcha_id = str(uuid.uuid4())
    _, image_data = await create_captcha_redis(captcha_id)
    return {"captcha_id": captcha_id, "image": image_data}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreateWithCaptcha,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with captcha verification."""
    from app.services.settings import is_registration_enabled
    
    ip = get_real_ip(request)
    
    # Rate limit: max 5 registrations per IP per hour
    is_allowed, count, remaining = await check_rate_limit(f"register:{ip}", 5, 3600)
    if not is_allowed:
        logger.warning(f"Registration rate limit exceeded for IP {ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="注册请求过于频繁，请稍后再试"
        )
    
    # Verify captcha FIRST (before any other validation)
    if not await verify_captcha_redis(user_data.captcha_id, user_data.captcha_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )
    
    # Check if registration is enabled
    if not await is_registration_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled"
        )
    
    # Input validation - username
    if not user_data.username or len(user_data.username) < 3 or len(user_data.username) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名长度必须在3-20个字符之间"
        )
    
    if not USERNAME_REGEX.match(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名只能包含字母、数字和下划线，且必须以字母开头"
        )
    
    # Input validation - email
    if not EMAIL_REGEX.match(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请输入有效的邮箱地址"
        )
    
    # Input validation - password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少8位"
        )
    if not re.search(r'[a-z]', user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含小写字母"
        )
    if not re.search(r'[A-Z]', user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含大写字母"
        )
    if not re.search(r'\d', user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含数字"
        )
    
    # Check if username or email already exists
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_data.username,
                User.email == user_data.email.lower()
            )
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate verification token
    verify_token = generate_verification_token()
    verify_token_expires = datetime.utcnow() + timedelta(hours=24)
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email.lower(),  # Normalize email to lowercase
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.USER,
        status=UserStatus.PENDING,
        email_verify_token=verify_token,
        email_verify_token_expires=verify_token_expires,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Send verification email
    await send_verification_email(user.email, user.username, verify_token)
    
    logger.info(f"New user registered: {user.username} from IP {ip}")
    
    # 记录审计日志
    await create_audit_log(
        db=db,
        action="register",
        ip_address=ip,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        user_agent=request.headers.get("User-Agent"),
        details=f"New user registered: {user.username}",
        log_status="success"
    )
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login and get access token."""
    ip = get_real_ip(request)
    
    # Debug: Log all relevant headers and detected IP
    logger.info(f"Login attempt - Detected IP: {ip}")
    logger.info(f"  X-Forwarded-For: {request.headers.get('X-Forwarded-For')}")
    logger.info(f"  X-Real-IP: {request.headers.get('X-Real-IP')}")
    logger.info(f"  CF-Connecting-IP: {request.headers.get('CF-Connecting-IP')}")
    logger.info(f"  Client host: {request.client.host if request.client else 'None'}")
    
    # Check login attempts
    is_blocked, attempts = await check_login_attempts(ip)
    logger.info(f"  Login attempts for {ip}: {attempts}, blocked: {is_blocked}")
    
    if is_blocked:
        logger.warning(f"Login blocked for IP {ip} after {attempts} attempts")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later."
        )
    
    # Find user by username or email
    result = await db.execute(
        select(User).where(
            or_(
                User.username == user_data.username,
                User.email == user_data.username
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        await record_failed_login(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check user status
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first"
        )
    
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been disabled"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked"
        )
    
    # Clear failed login attempts
    await clear_login_attempts(ip)
    
    # Reset failed attempts counter
    user.failed_login_attempts = 0
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = ip
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # 记录登录审计日志
    await create_audit_log(
        db=db,
        action="login",
        ip_address=ip,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        user_agent=request.headers.get("User-Agent"),
        details=f"User {user.username} logged in",
        log_status="success"
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify email address."""
    result = await db.execute(
        select(User).where(User.email_verify_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.email_verify_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    user.email_verified = True
    user.status = UserStatus.ACTIVE
    user.email_verify_token = None
    user.email_verify_token_expires = None
    
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    data: PasswordResetWithCaptcha,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email with captcha verification."""
    ip = get_real_ip(request)
    
    # Rate limit: max 3 password reset requests per IP per hour
    is_allowed, count, remaining = await check_rate_limit(f"forgot_password:{ip}", 3, 3600)
    if not is_allowed:
        logger.warning(f"Password reset rate limit exceeded for IP {ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="密码重置请求过于频繁，请稍后再试"
        )
    
    # Verify captcha FIRST
    if not await verify_captcha_redis(data.captcha_id, data.captcha_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )
    
    # Validate email format
    if not EMAIL_REGEX.match(data.email):
        # Still return success to prevent enumeration
        return {"message": "If the email exists, a password reset link has been sent"}
    
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if user and user.status == UserStatus.ACTIVE:
        # Additional rate limit: max 1 email per user per 5 minutes
        user_allowed, _, _ = await check_rate_limit(f"forgot_password_user:{user.id}", 1, 300)
        if user_allowed:
            reset_token = generate_verification_token()
            user.password_reset_token = reset_token
            user.password_reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            await db.commit()
            
            await send_password_reset_email(user.email, user.username, reset_token)
            logger.info(f"Password reset email sent to {user.email} from IP {ip}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    data: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using token."""
    ip = get_real_ip(request)
    
    # Rate limit: max 5 reset attempts per IP per hour
    is_allowed, count, remaining = await check_rate_limit(f"reset_password:{ip}", 5, 3600)
    if not is_allowed:
        logger.warning(f"Password reset rate limit exceeded for IP {ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="密码重置请求过于频繁，请稍后再试"
        )
    
    result = await db.execute(
        select(User).where(User.password_reset_token == data.token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if user.password_reset_token_expires < datetime.utcnow():
        # 清除过期token
        user.password_reset_token = None
        user.password_reset_token_expires = None
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # 验证新密码强度
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少8位"
        )
    if not re.search(r'[a-z]', data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含小写字母"
        )
    if not re.search(r'[A-Z]', data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含大写字母"
        )
    if not re.search(r'\d', data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须包含数字"
        )
    
    user.hashed_password = get_password_hash(data.new_password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    # 重置密码后清除登录失败计数
    user.failed_login_attempts = 0
    user.locked_until = None
    
    await db.commit()
    
    logger.info(f"Password reset successful for user {user.username} from IP {ip}")
    
    return {"message": "Password reset successfully"}
