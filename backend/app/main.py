from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from app.config import get_settings
from app.database import init_db
from app.redis import init_redis, close_redis
from app.api import auth, upload, images, albums, user
from app.api.admin import router as admin_router
from app.utils.rate_limit import get_real_ip, is_blacklisted

# Import all models to ensure they are registered with SQLAlchemy
from app.models import user as user_model
from app.models import image as image_model
from app.models import album as album_model
from app.models import settings as settings_model
from app.models import audit_log as audit_log_model
from app.models import backup as backup_model

settings = get_settings()

# Ensure uploads directory exists
os.makedirs(settings.upload_path, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    await init_redis()
    await init_db()
    # Load IP header settings
    from app.utils.rate_limit import refresh_ip_header_settings
    try:
        await refresh_ip_header_settings()
        logger.info("IP header settings loaded")
    except Exception as e:
        logger.warning(f"Failed to load IP header settings, using defaults: {e}")
    
    # Initialize backup scheduler
    try:
        from app.services.backup.scheduler import init_scheduler
        await init_scheduler()
        logger.info("Backup scheduler initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize backup scheduler: {e}")
    
    logger.info("Application started successfully")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    
    # Shutdown backup scheduler
    try:
        from app.services.backup.scheduler import shutdown_scheduler
        await shutdown_scheduler()
    except Exception as e:
        logger.warning(f"Error shutting down backup scheduler: {e}")
    
    await close_redis()
    logger.info("Application shut down")


app = FastAPI(
    title=settings.app_name,
    description="A secure image hosting service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else [settings.app_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Check IP blacklist
    ip = get_real_ip(request)
    if await is_blacklisted(ip):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Your IP has been temporarily blocked"}
        )
    
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Include routers
from app.api import appeal, gallery, download
app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(albums.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(appeal.router, prefix="/api")
app.include_router(gallery.router, prefix="/api")  # 公开画廊API
app.include_router(download.router, prefix="/api")  # 批量下载API
app.include_router(admin_router, prefix="/api")

# Dynamic image serving with status check (replaces static mount)
# This ensures rejected images cannot be accessed
from fastapi.responses import FileResponse
from app.database import AsyncSessionLocal
from app.models.image import Image, ImageStatus
from sqlalchemy import select

@app.get("/uploads/{file_path:path}")
async def serve_image(file_path: str):
    """
    动态图片访问端点 - 检查图片状态后再返回
    被拒绝的图片返回替换图或 403
    
    支持两种路径格式:
    - 旧格式: /uploads/abc123.png
    - 新格式: /uploads/2025/12/14/abc123.png (日期文件夹结构)
    """
    from fastapi.responses import RedirectResponse
    from app.services.settings import get_audit_violation_image
    
    # 安全检查：防止路径遍历攻击
    # 拒绝包含 .. 或以 / 开头的路径
    if '..' in file_path or file_path.startswith('/') or file_path.startswith('\\'):
        logger.warning(f"Path traversal attempt blocked: {file_path}")
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # 从路径中提取文件名 (最后一部分)
    # 例如: "2025/12/14/abc123.png" -> "abc123.png"
    # 或者: "abc123.png" -> "abc123.png"
    filename = file_path.split('/')[-1] if '/' in file_path else file_path
    
    if '.' not in filename:
        raise HTTPException(status_code=404, detail="Image not found")
    
    name_part = filename.rsplit('.', 1)[0]
    
    # 构建完整路径并验证它在 upload_path 内
    full_file_path = os.path.normpath(os.path.join(settings.upload_path, file_path))
    upload_path_normalized = os.path.normpath(settings.upload_path)
    
    # 确保最终路径在 upload_path 目录内（防止路径遍历）
    if not full_file_path.startswith(upload_path_normalized):
        logger.warning(f"Path escape attempt blocked: {file_path} -> {full_file_path}")
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # 查询数据库检查状态
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Image).where(Image.filename == name_part)
        )
        image = result.scalar_one_or_none()
        
        # 如果数据库中没有记录
        if not image:
            if os.path.isfile(full_file_path):
                return FileResponse(full_file_path)
            raise HTTPException(status_code=404, detail="Image not found")
        
        # 获取状态值 - 兼容多种情况
        # MySQL enum 可能返回字符串或 Enum 对象
        if hasattr(image.status, 'value'):
            status_str = image.status.value
        elif isinstance(image.status, str):
            status_str = image.status
        else:
            status_str = str(image.status)
        
        # 统一转小写比较
        status_str = status_str.lower()
        logger.info(f"Serving image {filename}, raw_status={image.status}, status_str={status_str}")
        
        # 被拒绝的图片 - 返回替换图或403
        if status_str == "rejected":
            logger.warning(f"BLOCKED: Access to rejected image: {file_path}")
            
            # 直接从数据库获取替换图URL
            replacement_url = await get_audit_violation_image()
            logger.info(f"Replacement URL: '{replacement_url}'")
            
            if replacement_url and replacement_url.strip():
                logger.info(f"Redirecting to replacement image: {replacement_url.strip()}")
                return RedirectResponse(
                    url=replacement_url.strip(),
                    status_code=302
                )
            else:
                logger.info("No replacement URL configured, returning 403")
                raise HTTPException(status_code=403, detail="Image removed due to policy violation")
        
        # 文件不存在 - 可能已被删除
        if not os.path.isfile(full_file_path):
            logger.warning(f"File not found on disk: {full_file_path}, status={status_str}")
            # 如果文件不存在，尝试返回替换图
            replacement_url = await get_audit_violation_image()
            if replacement_url and replacement_url.strip():
                return RedirectResponse(url=replacement_url.strip(), status_code=302)
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # 正常返回图片
        # 只有已审核通过的图片才允许 CDN 缓存
        if status_str == "approved":
            cache_control = "public, max-age=31536000"
        else:
            # pending 状态的图片不缓存，避免审核后 CDN 仍返回原图
            cache_control = "no-store, no-cache, must-revalidate, max-age=0"
        
        return FileResponse(full_file_path, media_type=image.mime_type, headers={
            "Cache-Control": cache_control,
            "CDN-Cache-Control": cache_control,  # 部分 CDN 支持
            "Cloudflare-CDN-Cache-Control": cache_control,  # Cloudflare 专用
        })


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Public site settings (no auth required)
@app.get("/api/site/settings")
async def get_public_site_settings():
    """Get public site settings for frontend."""
    from app.services.settings import get_public_settings
    return await get_public_settings()


# Root redirect
@app.get("/api")
async def api_root():
    from app.services.settings import get_site_name
    site_name = await get_site_name()
    return {
        "name": site_name,
        "version": "1.0.0",
        "docs": "/api/docs",
    }


# Serve frontend static files (for Docker deployment)
# This should be mounted last to avoid conflicts with API routes
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    from fastapi.responses import FileResponse
    
    # Serve static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    # Serve index.html for SPA routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve frontend SPA for all non-API routes."""
        # Skip API routes
        if full_path.startswith("api/") or full_path.startswith("uploads/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        # Try to serve static file first
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html for SPA routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return JSONResponse(status_code=404, content={"detail": "Not found"})
