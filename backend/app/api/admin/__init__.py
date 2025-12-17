from fastapi import APIRouter
from app.api.admin import dashboard, users, images, settings, audit, blacklist, backup, gallery

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(dashboard.router)
router.include_router(users.router)
router.include_router(images.router)
router.include_router(settings.router)
router.include_router(audit.router)
router.include_router(blacklist.router)
router.include_router(backup.router)
router.include_router(gallery.router)
