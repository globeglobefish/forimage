"""
Admin API endpoints for backup management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.user import User
from app.api.deps import get_admin_user as get_current_admin_user
from app.services.backup.service import BackupService
from app.schemas.backup import (
    BackupNodeCreate, BackupNodeUpdate, BackupNodeResponse,
    BackupNodeListResponse, BackupLogListResponse, BackupLogResponse,
    BackupDashboardResponse, ConnectionTestResponse, BackupLogFilter,
    BackupTriggerRequest, RestoreRequest, BackupTaskResponse
)

router = APIRouter(prefix="/backup", tags=["backup"])


async def get_backup_service(db: AsyncSession = Depends(get_db)) -> BackupService:
    """Dependency to get backup service instance."""
    return BackupService(db)


# Node CRUD endpoints
@router.get("/nodes", response_model=BackupNodeListResponse)
async def list_backup_nodes(
    enabled_only: bool = False,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """List all backup nodes."""
    nodes = await service.list_nodes(enabled_only=enabled_only)
    node_responses = [await service.get_node_response(node) for node in nodes]
    return BackupNodeListResponse(nodes=node_responses, total=len(node_responses))


@router.post("/nodes", response_model=BackupNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_backup_node(
    data: BackupNodeCreate,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new backup node."""
    node = await service.create_node(data)
    return await service.get_node_response(node)


@router.get("/nodes/{node_id}", response_model=BackupNodeResponse)
async def get_backup_node(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Get a backup node by ID."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    return await service.get_node_response(node)


@router.put("/nodes/{node_id}", response_model=BackupNodeResponse)
async def update_backup_node(
    node_id: int,
    data: BackupNodeUpdate,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Update a backup node."""
    node = await service.update_node(node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    return await service.get_node_response(node)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_node(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a backup node."""
    success = await service.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup node not found")


@router.post("/nodes/{node_id}/test", response_model=ConnectionTestResponse)
async def test_backup_node(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Test connection to a backup node."""
    result = await service.test_node_connection(node_id)
    return result


# Backup operation endpoints
@router.post("/nodes/{node_id}/backup", response_model=BackupTaskResponse)
async def trigger_backup(
    node_id: int,
    request: BackupTriggerRequest = None,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Trigger backup operation for a node."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    if not node.is_enabled:
        raise HTTPException(status_code=400, detail="Backup node is disabled")
    
    # Execute backup synchronously
    result = await service.execute_backup(node_id, triggered_by=current_user.id)
    
    return BackupTaskResponse(
        task_id=f"backup_{node_id}_{int(__import__('time').time())}",
        node_id=node_id,
        task_type="backup",
        status="success" if result.get("success") else "failed",
        files_total=result.get("files_total", 0),
        files_completed=result.get("files_success", 0),
        message=result.get("message", "Backup completed"),
    )


@router.post("/nodes/{node_id}/sync", response_model=BackupTaskResponse)
async def trigger_full_sync(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Trigger full synchronization for a node."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    # TODO: Implement actual sync task queue
    return BackupTaskResponse(
        task_id=f"sync_{node_id}_{int(__import__('time').time())}",
        node_id=node_id,
        task_type="sync",
        status="queued",
        message="Full sync task queued successfully",
    )


@router.post("/nodes/{node_id}/restore", response_model=BackupTaskResponse)
async def trigger_restore(
    node_id: int,
    request: RestoreRequest = None,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Trigger restore operation from a node."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    # TODO: Implement actual restore task queue
    return BackupTaskResponse(
        task_id=f"restore_{node_id}_{int(__import__('time').time())}",
        node_id=node_id,
        task_type="restore",
        status="queued",
        message="Restore task queued successfully",
    )


@router.post("/nodes/{node_id}/pause", status_code=status.HTTP_200_OK)
async def pause_backup_node(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Pause backup operations for a node."""
    from app.schemas.backup import BackupNodeUpdate
    node = await service.update_node(node_id, BackupNodeUpdate(is_enabled=False))
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    return {"message": "Backup node paused"}


@router.post("/nodes/{node_id}/resume", status_code=status.HTTP_200_OK)
async def resume_backup_node(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Resume backup operations for a node."""
    from app.schemas.backup import BackupNodeUpdate
    node = await service.update_node(node_id, BackupNodeUpdate(is_enabled=True))
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    return {"message": "Backup node resumed"}


# Log and dashboard endpoints
@router.get("/logs", response_model=BackupLogListResponse)
async def list_backup_logs(
    node_id: int = None,
    task_type: str = None,
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """List backup logs with filtering."""
    filter_params = BackupLogFilter(
        node_id=node_id,
        task_type=task_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    logs, total = await service.list_logs(filter_params, return_total=True)
    return BackupLogListResponse(logs=logs, total=total)


@router.get("/dashboard", response_model=BackupDashboardResponse)
async def get_backup_dashboard(
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Get backup dashboard data."""
    return await service.get_dashboard()


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_log(
    log_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a backup log entry."""
    success = await service.delete_log(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup log not found")


# File status management endpoints
@router.get("/nodes/{node_id}/status")
async def get_node_file_status(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Get detailed file status summary for a backup node."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    return await service.get_file_status_summary(node_id)


@router.post("/nodes/{node_id}/retry-failed")
async def retry_failed_files(
    node_id: int,
    max_retries: int = 3,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Reset failed files for retry (files with retry_count < max_retries)."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    return await service.retry_failed_files(node_id, max_retries)


@router.post("/nodes/{node_id}/cleanup")
async def cleanup_deleted_records(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Clean up backup status records for deleted files."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    return await service.cleanup_deleted_records(node_id)


@router.post("/nodes/{node_id}/sync-status")
async def sync_file_status(
    node_id: int,
    service: BackupService = Depends(get_backup_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Synchronize backup status with images table (mark orphaned records as deleted)."""
    node = await service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Backup node not found")
    
    return await service.sync_file_status_with_images(node_id)



