"""
Backup service for managing backup nodes and operations.
"""
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backup import (
    BackupNode, BackupFileStatus, BackupLog,
    BackupProtocol, SyncStrategy, SyncStatus,
    FileBackupStatus, BackupTaskType, BackupTaskStatus
)
from app.models.image import Image
from app.schemas.backup import (
    BackupNodeCreate, BackupNodeUpdate, BackupNodeResponse,
    BackupLogResponse, BackupDashboardResponse, ConnectionTestResponse,
    BackupLogFilter
)
from app.utils.encryption import encrypt_config, decrypt_config, mask_config
from app.services.backup.factory import get_backup_backend


class BackupService:
    """Service for managing backup nodes and operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_node(self, data: BackupNodeCreate) -> BackupNode:
        """Create a new backup node."""
        # Encrypt connection config
        encrypted_config = encrypt_config(data.connection_config)
        
        node = BackupNode(
            name=data.name,
            protocol=data.protocol,
            connection_config=encrypted_config,
            sync_strategy=data.sync_strategy,
            schedule_cron=data.schedule_cron,
            file_types=data.file_types,
            max_bandwidth=data.max_bandwidth,
            max_concurrent=data.max_concurrent,
            is_enabled=data.is_enabled,
        )
        
        self.db.add(node)
        await self.db.commit()
        await self.db.refresh(node)
        
        return node
    
    async def update_node(self, node_id: int, data: BackupNodeUpdate) -> Optional[BackupNode]:
        """Update a backup node."""
        node = await self.get_node(node_id)
        if not node:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle connection_config update - preserve sensitive fields if empty or masked
        if "connection_config" in update_data and update_data["connection_config"]:
            new_config = update_data["connection_config"]
            
            # Get existing config to preserve sensitive fields
            try:
                existing_config = decrypt_config(node.connection_config)
            except Exception:
                existing_config = {}
            
            # Sensitive fields that should be preserved if empty or masked
            sensitive_fields = ['password', 'secret_key', 'private_key', 'access_key']
            
            for field in sensitive_fields:
                new_value = new_config.get(field)
                existing_value = existing_config.get(field)
                
                # Preserve existing value if:
                # 1. New value is empty/None
                # 2. New value starts with '*' (masked value)
                if existing_value and (not new_value or (isinstance(new_value, str) and new_value.startswith('*'))):
                    new_config[field] = existing_value
            
            update_data["connection_config"] = encrypt_config(new_config)
        
        for key, value in update_data.items():
            setattr(node, key, value)
        
        await self.db.commit()
        await self.db.refresh(node)
        
        # Update scheduler if sync strategy or schedule changed
        if "sync_strategy" in update_data or "schedule_cron" in update_data or "is_enabled" in update_data:
            try:
                from app.services.backup.scheduler import update_node_schedule
                if node.is_enabled and node.sync_strategy == SyncStrategy.SCHEDULED:
                    await update_node_schedule(node_id, node.sync_strategy.value, node.schedule_cron)
                else:
                    await update_node_schedule(node_id, node.sync_strategy.value, None)
            except Exception as e:
                logger.warning(f"Failed to update scheduler for node {node_id}: {e}")
        
        return node
    
    async def delete_node(self, node_id: int) -> bool:
        """Delete a backup node and all associated data."""
        node = await self.get_node(node_id)
        if not node:
            return False
        
        await self.db.delete(node)
        await self.db.commit()
        
        return True
    
    async def get_node(self, node_id: int) -> Optional[BackupNode]:
        """Get a backup node by ID."""
        result = await self.db.execute(
            select(BackupNode).where(BackupNode.id == node_id)
        )
        return result.scalar_one_or_none()
    
    async def get_node_with_config(self, node_id: int) -> Optional[tuple[BackupNode, Dict[str, Any]]]:
        """Get a backup node with decrypted config."""
        node = await self.get_node(node_id)
        if not node:
            return None
        
        config = decrypt_config(node.connection_config)
        return node, config
    
    async def list_nodes(self, enabled_only: bool = False) -> List[BackupNode]:
        """List all backup nodes."""
        query = select(BackupNode)
        if enabled_only:
            query = query.where(BackupNode.is_enabled == True)
        query = query.order_by(BackupNode.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_node_response(self, node: BackupNode) -> BackupNodeResponse:
        """Convert node to response with masked config."""
        # Decrypt and mask config
        try:
            config = decrypt_config(node.connection_config)
            masked_config = mask_config(config)
        except Exception:
            masked_config = {}
        
        # Get real-time synced file count from backup_file_status table
        # This is more accurate than node.total_files which only updates after backup tasks
        result = await self.db.execute(
            select(
                func.count(BackupFileStatus.id),
                func.coalesce(func.sum(BackupFileStatus.file_size), 0)
            )
            .where(
                and_(
                    BackupFileStatus.node_id == node.id,
                    BackupFileStatus.status == FileBackupStatus.SYNCED
                )
            )
        )
        row = result.one()
        real_total_files = row[0] or 0
        real_total_bytes = row[1] or 0
        
        return BackupNodeResponse(
            id=node.id,
            name=node.name,
            protocol=node.protocol,
            is_enabled=node.is_enabled,
            sync_strategy=node.sync_strategy,
            schedule_cron=node.schedule_cron,
            file_types=node.file_types,
            max_bandwidth=node.max_bandwidth,
            max_concurrent=node.max_concurrent,
            last_sync_at=node.last_sync_at,
            last_sync_status=node.last_sync_status.value if node.last_sync_status else None,
            total_files=real_total_files,
            total_bytes=real_total_bytes,
            created_at=node.created_at,
            updated_at=node.updated_at,
            connection_config_masked=masked_config,
        )
    
    async def test_node_connection(self, node_id: int) -> ConnectionTestResponse:
        """Test connection to a backup node."""
        result = await self.get_node_with_config(node_id)
        if not result:
            return ConnectionTestResponse(
                success=False,
                message="Backup node not found",
                latency_ms=None,
                details={},
            )
        
        node, config = result
        
        try:
            backend = get_backup_backend(node.protocol, config)
            async with backend:
                test_result = await backend.test_connection()
            
            # Log the test
            await self._create_log(
                node_id=node_id,
                task_type=BackupTaskType.TEST,
                status=BackupTaskStatus.SUCCESS if test_result.success else BackupTaskStatus.FAILED,
                error_details=None if test_result.success else test_result.message,
            )
            
            return ConnectionTestResponse(
                success=test_result.success,
                message=test_result.message,
                latency_ms=test_result.latency_ms,
                details=test_result.details,
            )
        except Exception as e:
            await self._create_log(
                node_id=node_id,
                task_type=BackupTaskType.TEST,
                status=BackupTaskStatus.FAILED,
                error_details=str(e),
            )
            
            return ConnectionTestResponse(
                success=False,
                message=f"Connection test failed: {str(e)}",
                latency_ms=None,
                details={"error": str(e)},
            )
    
    async def get_node_status(self, node_id: int) -> Dict[str, Any]:
        """Get detailed status of a backup node."""
        node = await self.get_node(node_id)
        if not node:
            return {}
        
        # Count files by status with real-time query
        status_counts = await self.db.execute(
            select(
                BackupFileStatus.status,
                func.count(BackupFileStatus.id),
                func.coalesce(func.sum(BackupFileStatus.file_size), 0)
            )
            .where(BackupFileStatus.node_id == node_id)
            .group_by(BackupFileStatus.status)
        )
        
        counts = {}
        bytes_by_status = {}
        for row in status_counts:
            counts[row[0].value] = row[1]
            bytes_by_status[row[0].value] = row[2]
        
        # Use real-time synced count instead of cached node.total_files
        real_total_files = counts.get("synced", 0)
        real_total_bytes = bytes_by_status.get("synced", 0)
        
        return {
            "node_id": node_id,
            "name": node.name,
            "is_enabled": node.is_enabled,
            "last_sync_at": node.last_sync_at,
            "last_sync_status": node.last_sync_status.value if node.last_sync_status else None,
            "total_files": real_total_files,
            "total_bytes": real_total_bytes,
            "files_pending": counts.get("pending", 0),
            "files_synced": counts.get("synced", 0),
            "files_failed": counts.get("failed", 0),
        }
    
    async def get_dashboard(self) -> BackupDashboardResponse:
        """Get backup dashboard data."""
        nodes = await self.list_nodes()
        
        total_nodes = len(nodes)
        enabled_nodes = sum(1 for n in nodes if n.is_enabled)
        
        # Get real-time synced file count from backup_file_status table
        # This is more accurate than node.total_files which only updates after backup tasks
        result = await self.db.execute(
            select(
                func.count(BackupFileStatus.id),
                func.coalesce(func.sum(BackupFileStatus.file_size), 0)
            )
            .where(BackupFileStatus.status == FileBackupStatus.SYNCED)
        )
        row = result.one()
        total_files = row[0] or 0
        total_bytes = row[1] or 0
        
        # Get last backup time
        last_backup = max(
            (n.last_sync_at for n in nodes if n.last_sync_at),
            default=None
        )
        
        # Get node statuses
        nodes_status = []
        for node in nodes:
            status = await self.get_node_status(node.id)
            nodes_status.append(status)
        
        # Get recent logs
        logs = await self.list_logs(BackupLogFilter(page_size=10))
        
        return BackupDashboardResponse(
            total_nodes=total_nodes,
            enabled_nodes=enabled_nodes,
            total_files_backed_up=total_files,
            total_bytes_backed_up=total_bytes,
            last_backup_at=last_backup,
            nodes_status=nodes_status,
            recent_logs=logs,
        )
    
    async def list_logs(
        self,
        filter_params: BackupLogFilter,
        return_total: bool = False
    ) -> tuple[List[BackupLogResponse], int] | List[BackupLogResponse]:
        """List backup logs with filtering."""
        from sqlalchemy.orm import joinedload
        base_query = select(BackupLog).options(joinedload(BackupLog.node))
        
        conditions = []
        if filter_params.node_id:
            conditions.append(BackupLog.node_id == filter_params.node_id)
        if filter_params.task_type:
            conditions.append(BackupLog.task_type == filter_params.task_type)
        if filter_params.status:
            conditions.append(BackupLog.status == filter_params.status)
        if filter_params.start_date:
            conditions.append(BackupLog.created_at >= filter_params.start_date)
        if filter_params.end_date:
            conditions.append(BackupLog.created_at <= filter_params.end_date)
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Get total count if requested
        total = 0
        if return_total:
            count_query = select(func.count(BackupLog.id)).select_from(BackupLog)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0
        
        query = base_query.order_by(BackupLog.created_at.desc())
        
        # Pagination
        offset = (filter_params.page - 1) * filter_params.page_size
        query = query.offset(offset).limit(filter_params.page_size)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        log_responses = [
            BackupLogResponse(
                id=log.id,
                node_id=log.node_id,
                node_name=log.node.name if log.node else None,
                task_type=log.task_type.value,
                status=log.status.value,
                files_total=log.files_total,
                files_success=log.files_success,
                files_failed=log.files_failed,
                bytes_transferred=log.bytes_transferred,
                started_at=log.started_at,
                completed_at=log.completed_at,
                duration_seconds=log.duration_seconds,
                error_details=log.error_details,
                triggered_by=log.triggered_by,
                created_at=log.created_at,
            )
            for log in logs
        ]
        
        if return_total:
            return log_responses, total
        return log_responses
    
    async def _create_log(
        self,
        node_id: int,
        task_type: BackupTaskType,
        status: BackupTaskStatus,
        files_total: int = 0,
        files_success: int = 0,
        files_failed: int = 0,
        bytes_transferred: int = 0,
        error_details: Optional[str] = None,
        triggered_by: Optional[int] = None,
    ) -> BackupLog:
        """Create a backup log entry."""
        now = datetime.utcnow()
        
        log = BackupLog(
            node_id=node_id,
            task_type=task_type,
            status=status,
            files_total=files_total,
            files_success=files_success,
            files_failed=files_failed,
            bytes_transferred=bytes_transferred,
            started_at=now,
            completed_at=now if status != BackupTaskStatus.RUNNING else None,
            duration_seconds=0 if status != BackupTaskStatus.RUNNING else None,
            error_details=error_details,
            triggered_by=triggered_by,
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    
    async def delete_log(self, log_id: int) -> bool:
        """Delete a backup log entry."""
        result = await self.db.execute(
            select(BackupLog).where(BackupLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if not log:
            return False
        
        await self.db.delete(log)
        await self.db.commit()
        return True
    
    async def update_node_stats(self, node_id: int) -> None:
        """Update node statistics from file status table."""
        await self._recalculate_node_stats(node_id)
        await self.db.commit()
    
    async def get_file_status_summary(self, node_id: int) -> Dict[str, Any]:
        """Get detailed file status summary for a node."""
        # Count files by status
        result = await self.db.execute(
            select(
                BackupFileStatus.status,
                func.count(BackupFileStatus.id),
                func.coalesce(func.sum(BackupFileStatus.file_size), 0)
            )
            .where(BackupFileStatus.node_id == node_id)
            .group_by(BackupFileStatus.status)
        )
        
        summary = {
            "synced": {"count": 0, "bytes": 0},
            "pending": {"count": 0, "bytes": 0},
            "failed": {"count": 0, "bytes": 0},
            "deleted": {"count": 0, "bytes": 0},
        }
        
        for row in result:
            status, count, bytes_sum = row
            summary[status.value] = {"count": count, "bytes": bytes_sum}
        
        # Get total images in system
        total_images_result = await self.db.execute(select(func.count(Image.id)))
        total_images = total_images_result.scalar() or 0
        
        # Calculate untracked (images not in backup_file_status for this node)
        tracked_count = sum(s["count"] for s in summary.values())
        untracked = total_images - tracked_count
        
        return {
            "node_id": node_id,
            "total_images": total_images,
            "synced": summary["synced"],
            "pending": summary["pending"],
            "failed": summary["failed"],
            "deleted": summary["deleted"],
            "untracked": untracked,
        }
    
    async def retry_failed_files(self, node_id: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        Reset failed files for retry (excluding those with too many retries).
        Files with retry_count >= max_retries will be skipped.
        """
        # Get failed files that haven't exceeded max retries
        result = await self.db.execute(
            select(BackupFileStatus).where(
                and_(
                    BackupFileStatus.node_id == node_id,
                    BackupFileStatus.status == FileBackupStatus.FAILED,
                    BackupFileStatus.retry_count < max_retries
                )
            )
        )
        
        failed_statuses = list(result.scalars().all())
        reset_count = 0
        
        for status in failed_statuses:
            status.status = FileBackupStatus.PENDING
            status.error_message = None
            reset_count += 1
        
        await self.db.commit()
        
        return {
            "reset_count": reset_count,
            "message": f"Reset {reset_count} failed files for retry"
        }
    
    async def cleanup_deleted_records(self, node_id: int) -> Dict[str, Any]:
        """
        Remove backup status records for files marked as DELETED.
        This cleans up records for files that no longer exist locally.
        """
        result = await self.db.execute(
            select(BackupFileStatus).where(
                and_(
                    BackupFileStatus.node_id == node_id,
                    BackupFileStatus.status == FileBackupStatus.DELETED
                )
            )
        )
        
        deleted_statuses = list(result.scalars().all())
        deleted_count = len(deleted_statuses)
        
        for status in deleted_statuses:
            await self.db.delete(status)
        
        await self.db.commit()
        
        return {
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} deleted file records"
        }
    
    async def sync_file_status_with_images(self, node_id: int) -> Dict[str, Any]:
        """
        Synchronize backup_file_status with images table.
        - Mark status as DELETED if image no longer exists in images table
        - This handles cases where images were deleted from the database
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Get all backup statuses for this node
        result = await self.db.execute(
            select(BackupFileStatus).where(
                and_(
                    BackupFileStatus.node_id == node_id,
                    BackupFileStatus.status != FileBackupStatus.DELETED
                )
            )
        )
        
        statuses = list(result.scalars().all())
        
        # Get all image IDs
        images_result = await self.db.execute(select(Image.id))
        existing_image_ids = {row[0] for row in images_result}
        
        orphaned_count = 0
        for status in statuses:
            if status.image_id not in existing_image_ids:
                status.status = FileBackupStatus.DELETED
                status.error_message = "Image deleted from database"
                orphaned_count += 1
                logger.info(f"Marked orphaned backup status as deleted: image_id={status.image_id}")
        
        await self.db.commit()
        
        return {
            "orphaned_count": orphaned_count,
            "message": f"Marked {orphaned_count} orphaned records as deleted"
        }
    
    async def execute_backup(self, node_id: int, triggered_by: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute backup for all pending images to a node.
        
        Improved logic:
        1. Skip files already synced (status=SYNCED)
        2. Skip files marked as DELETED (local file doesn't exist)
        3. Mark missing local files as DELETED to avoid repeated failures
        4. Track failed files with retry count
        5. Only count actual backup attempts in statistics
        """
        import os
        import logging
        from app.config import get_settings
        
        logger = logging.getLogger(__name__)
        settings = get_settings()
        
        result = await self.get_node_with_config(node_id)
        if not result:
            return {"success": False, "message": "Node not found"}
        
        node, config = result
        
        # Create log entry
        log = await self._create_log(
            node_id=node_id,
            task_type=BackupTaskType.BACKUP,
            status=BackupTaskStatus.RUNNING,
            triggered_by=triggered_by,
        )
        
        files_total = 0
        files_success = 0
        files_failed = 0
        files_skipped = 0
        bytes_transferred = 0
        errors = []
        
        try:
            # Get existing backup statuses for this node
            existing_query = select(BackupFileStatus).where(
                BackupFileStatus.node_id == node_id
            )
            existing_result = await self.db.execute(existing_query)
            existing_statuses = {s.image_id: s for s in existing_result.scalars().all()}
            
            # Get IDs to exclude: already synced or marked as deleted
            exclude_ids = {
                img_id for img_id, status in existing_statuses.items()
                if status.status in (FileBackupStatus.SYNCED, FileBackupStatus.DELETED)
            }
            
            # Get images to backup (excluding already synced/deleted)
            if exclude_ids:
                images_query = select(Image).where(Image.id.notin_(exclude_ids))
            else:
                images_query = select(Image)
            
            images_result = await self.db.execute(images_query)
            images = list(images_result.scalars().all())
            
            # Filter out images that don't exist locally and mark them
            valid_images = []
            for image in images:
                # Use file_path which includes date folder structure (e.g., "2025/12/14/abc123.png")
                local_path = os.path.join(settings.upload_path, image.file_path)
                
                if not os.path.exists(local_path):
                    # Mark as DELETED so we don't try again
                    existing_status = existing_statuses.get(image.id)
                    if existing_status:
                        existing_status.status = FileBackupStatus.DELETED
                        existing_status.error_message = "Local file not found"
                        existing_status.updated_at = datetime.utcnow()
                    else:
                        deleted_status = BackupFileStatus(
                            node_id=node_id,
                            image_id=image.id,
                            remote_path=image.file_path,  # Preserve folder structure
                            file_size=0,
                            status=FileBackupStatus.DELETED,
                            error_message="Local file not found",
                        )
                        self.db.add(deleted_status)
                    
                    files_skipped += 1
                    logger.info(f"Skipped missing file: {image.filename} (marked as DELETED)")
                else:
                    valid_images.append(image)
            
            # Commit the DELETED status updates
            await self.db.commit()
            
            files_total = len(valid_images)
            
            if files_total == 0:
                log.status = BackupTaskStatus.SUCCESS
                log.files_total = 0
                log.files_success = 0
                log.files_failed = 0
                log.completed_at = datetime.utcnow()
                log.duration_seconds = 0
                await self.db.commit()
                
                message = "No files to backup"
                if files_skipped > 0:
                    message = f"No files to backup ({files_skipped} missing files marked as deleted)"
                
                return {
                    "success": True,
                    "message": message,
                    "files_total": 0,
                    "files_skipped": files_skipped,
                }
            
            # Get backend
            backend = get_backup_backend(node.protocol, config)
            
            async with backend:
                for image in valid_images:
                    try:
                        # Build local path using file_path (includes date folder structure)
                        local_path = os.path.join(settings.upload_path, image.file_path)
                        
                        # Double-check file exists (could be deleted during backup)
                        if not os.path.exists(local_path):
                            logger.warning(f"File disappeared during backup: {local_path}")
                            files_failed += 1
                            errors.append(f"File disappeared: {image.filename}")
                            continue
                        
                        # Get file size for accurate tracking
                        file_size = os.path.getsize(local_path)
                        
                        # Build remote path - preserve folder structure for date-based paths
                        remote_path = image.file_path
                        
                        # Upload file
                        upload_result = await backend.upload(local_path, remote_path)
                        
                        # Get or create file status record
                        existing_status = existing_statuses.get(image.id)
                        
                        if upload_result.success:
                            if existing_status:
                                existing_status.status = FileBackupStatus.SYNCED
                                existing_status.remote_path = upload_result.remote_path or remote_path
                                existing_status.file_size = upload_result.bytes_transferred or file_size
                                existing_status.checksum = upload_result.checksum
                                existing_status.last_sync_at = datetime.utcnow()
                                existing_status.error_message = None
                                existing_status.retry_count = 0
                            else:
                                file_status = BackupFileStatus(
                                    node_id=node_id,
                                    image_id=image.id,
                                    remote_path=upload_result.remote_path or remote_path,
                                    file_size=upload_result.bytes_transferred or file_size,
                                    checksum=upload_result.checksum,
                                    status=FileBackupStatus.SYNCED,
                                    last_sync_at=datetime.utcnow(),
                                )
                                self.db.add(file_status)
                            
                            files_success += 1
                            bytes_transferred += upload_result.bytes_transferred or file_size
                            logger.info(f"Backed up: {image.filename}")
                        else:
                            # Record failure with retry count
                            error_msg = upload_result.error_message or "Unknown error"
                            
                            if existing_status:
                                existing_status.status = FileBackupStatus.FAILED
                                existing_status.error_message = error_msg
                                existing_status.retry_count += 1
                            else:
                                file_status = BackupFileStatus(
                                    node_id=node_id,
                                    image_id=image.id,
                                    remote_path=remote_path,
                                    file_size=file_size,
                                    status=FileBackupStatus.FAILED,
                                    error_message=error_msg,
                                    retry_count=1,
                                )
                                self.db.add(file_status)
                            
                            files_failed += 1
                            errors.append(f"{image.filename}: {error_msg}")
                            logger.error(f"Failed to backup {image.filename}: {error_msg}")
                    
                    except Exception as e:
                        error_msg = str(e)
                        existing_status = existing_statuses.get(image.id)
                        
                        if existing_status:
                            existing_status.status = FileBackupStatus.FAILED
                            existing_status.error_message = error_msg
                            existing_status.retry_count += 1
                        else:
                            file_status = BackupFileStatus(
                                node_id=node_id,
                                image_id=image.id,
                                remote_path=image.file_path,  # Preserve folder structure
                                file_size=0,
                                status=FileBackupStatus.FAILED,
                                error_message=error_msg,
                                retry_count=1,
                            )
                            self.db.add(file_status)
                        
                        files_failed += 1
                        errors.append(f"{image.filename}: {error_msg}")
                        logger.error(f"Error backing up {image.filename}: {e}")
            
            # Update log
            now = datetime.utcnow()
            log.status = BackupTaskStatus.SUCCESS if files_failed == 0 else (
                BackupTaskStatus.PARTIAL if files_success > 0 else BackupTaskStatus.FAILED
            )
            log.files_total = files_total
            log.files_success = files_success
            log.files_failed = files_failed
            log.bytes_transferred = bytes_transferred
            log.completed_at = now
            log.duration_seconds = int((now - log.started_at).total_seconds())
            log.error_details = json.dumps(errors) if errors else None
            
            # Update node stats - recalculate from actual synced files
            await self._recalculate_node_stats(node_id, node)
            
            # Update last sync info
            node.last_sync_at = now
            node.last_sync_status = SyncStatus.SUCCESS if files_failed == 0 else (
                SyncStatus.PARTIAL if files_success > 0 else SyncStatus.FAILED
            )
            
            await self.db.commit()
            
            message = f"Backup completed: {files_success}/{files_total} files"
            if files_skipped > 0:
                message += f" ({files_skipped} missing files skipped)"
            
            return {
                "success": files_failed == 0,
                "message": message,
                "files_total": files_total,
                "files_success": files_success,
                "files_failed": files_failed,
                "files_skipped": files_skipped,
                "bytes_transferred": bytes_transferred,
            }
        
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            log.status = BackupTaskStatus.FAILED
            log.error_details = str(e)
            log.completed_at = datetime.utcnow()
            await self.db.commit()
            
            return {"success": False, "message": str(e)}
    
    async def _recalculate_node_stats(self, node_id: int, node: BackupNode = None) -> None:
        """Recalculate node statistics from actual synced files.
        
        Args:
            node_id: The node ID to recalculate stats for
            node: Optional node object to update directly (avoids re-query)
        """
        result = await self.db.execute(
            select(
                func.count(BackupFileStatus.id),
                func.coalesce(func.sum(BackupFileStatus.file_size), 0)
            )
            .where(
                and_(
                    BackupFileStatus.node_id == node_id,
                    BackupFileStatus.status == FileBackupStatus.SYNCED
                )
            )
        )
        
        row = result.one()
        total_files, total_bytes = row
        
        # Use provided node or fetch it
        if node is None:
            node = await self.get_node(node_id)
        
        if node:
            node.total_files = total_files
            node.total_bytes = total_bytes
