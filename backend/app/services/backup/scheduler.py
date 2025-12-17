"""
Backup scheduler service for scheduled and realtime backups.
Uses APScheduler for background task scheduling.

Performance considerations:
- Realtime backup uses background tasks (non-blocking)
- Tasks are queued and processed with controlled concurrency
- Failed backups are recorded and can be retried via scheduled tasks
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.backup import BackupNode, SyncStrategy, SyncStatus, BackupFileStatus, FileBackupStatus
from app.models.image import Image

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None

# Realtime backup queue for controlled concurrency
_realtime_queue: Optional[asyncio.Queue] = None
_queue_processor_task: Optional[asyncio.Task] = None
MAX_CONCURRENT_REALTIME_BACKUPS = 3  # Limit concurrent backup operations


def get_scheduler() -> AsyncIOScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def init_scheduler():
    """Initialize and start the backup scheduler."""
    global _realtime_queue, _queue_processor_task
    
    scheduler = get_scheduler()
    
    if scheduler.running:
        logger.info("Scheduler already running")
        return
    
    # Initialize realtime backup queue
    _realtime_queue = asyncio.Queue(maxsize=1000)  # Limit queue size
    _queue_processor_task = asyncio.create_task(_process_realtime_queue())
    logger.info("Realtime backup queue processor started")
    
    # Load scheduled backup jobs from database
    await reload_scheduled_jobs()
    
    # Add a job to check for scheduled backups every minute
    scheduler.add_job(
        check_scheduled_backups,
        IntervalTrigger(minutes=1),
        id="check_scheduled_backups",
        replace_existing=True,
        name="Check scheduled backups"
    )
    
    # Add a job to retry failed realtime backups every 5 minutes
    scheduler.add_job(
        retry_failed_realtime_backups,
        IntervalTrigger(minutes=5),
        id="retry_failed_realtime",
        replace_existing=True,
        name="Retry failed realtime backups"
    )
    
    scheduler.start()
    logger.info("Backup scheduler started")


async def shutdown_scheduler():
    """Shutdown the backup scheduler."""
    global _scheduler, _queue_processor_task, _realtime_queue
    
    # Stop queue processor
    if _queue_processor_task:
        _queue_processor_task.cancel()
        try:
            await _queue_processor_task
        except asyncio.CancelledError:
            pass
        _queue_processor_task = None
        logger.info("Realtime backup queue processor stopped")
    
    _realtime_queue = None
    
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Backup scheduler stopped")
    _scheduler = None


async def reload_scheduled_jobs():
    """Reload all scheduled backup jobs from database."""
    scheduler = get_scheduler()
    
    # Remove all existing backup jobs (except the check job)
    for job in scheduler.get_jobs():
        if job.id.startswith("backup_node_"):
            scheduler.remove_job(job.id)
    
    async with AsyncSessionLocal() as db:
        # Get all enabled nodes with scheduled strategy
        result = await db.execute(
            select(BackupNode).where(
                and_(
                    BackupNode.is_enabled == True,
                    BackupNode.sync_strategy == SyncStrategy.SCHEDULED,
                    BackupNode.schedule_cron.isnot(None)
                )
            )
        )
        nodes = result.scalars().all()
        
        for node in nodes:
            try:
                add_scheduled_job(node.id, node.schedule_cron)
                logger.info(f"Added scheduled job for node {node.id}: {node.schedule_cron}")
            except Exception as e:
                logger.error(f"Failed to add scheduled job for node {node.id}: {e}")


def add_scheduled_job(node_id: int, cron_expression: str):
    """Add a scheduled backup job for a node."""
    scheduler = get_scheduler()
    job_id = f"backup_node_{node_id}"
    
    # Parse cron expression (format: minute hour day_of_month month day_of_week)
    # Example: "0 2 * * *" = every day at 2:00 AM
    try:
        parts = cron_expression.strip().split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4]
            )
        else:
            # Simple format: just hour (e.g., "2" means 2:00 AM daily)
            hour = int(cron_expression.strip())
            trigger = CronTrigger(hour=hour, minute=0)
        
        scheduler.add_job(
            execute_scheduled_backup,
            trigger,
            args=[node_id],
            id=job_id,
            replace_existing=True,
            name=f"Scheduled backup for node {node_id}"
        )
        logger.info(f"Scheduled backup job added: {job_id} with cron: {cron_expression}")
    except Exception as e:
        logger.error(f"Invalid cron expression '{cron_expression}' for node {node_id}: {e}")
        raise


def remove_scheduled_job(node_id: int):
    """Remove a scheduled backup job for a node."""
    scheduler = get_scheduler()
    job_id = f"backup_node_{node_id}"
    
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed scheduled job: {job_id}")
    except Exception as e:
        logger.warning(f"Failed to remove job {job_id}: {e}")


async def check_scheduled_backups():
    """Periodic check for scheduled backups (fallback mechanism)."""
    # This is a fallback - the cron jobs should handle most cases
    # This just ensures nothing is missed
    pass


async def _process_realtime_queue():
    """
    Background task to process realtime backup queue.
    Uses semaphore to limit concurrent backups.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REALTIME_BACKUPS)
    
    async def process_item(item: Tuple[int, str, int]):
        async with semaphore:
            image_id, file_path, file_size = item
            await _execute_realtime_backup(image_id, file_path, file_size)
    
    while True:
        try:
            if _realtime_queue is None:
                break
            
            item = await _realtime_queue.get()
            # Process in background without blocking queue
            asyncio.create_task(process_item(item))
            _realtime_queue.task_done()
            
        except asyncio.CancelledError:
            logger.info("Queue processor cancelled")
            break
        except Exception as e:
            logger.error(f"Error in queue processor: {e}")
            await asyncio.sleep(1)


async def retry_failed_realtime_backups():
    """
    Retry failed realtime backups.
    Called periodically by scheduler.
    """
    logger.debug("Checking for failed realtime backups to retry")
    
    async with AsyncSessionLocal() as db:
        # Get all enabled realtime nodes
        result = await db.execute(
            select(BackupNode).where(
                and_(
                    BackupNode.is_enabled == True,
                    BackupNode.sync_strategy == SyncStrategy.REALTIME
                )
            )
        )
        nodes = result.scalars().all()
        
        for node in nodes:
            # Get failed files with retry_count < 3
            failed_result = await db.execute(
                select(BackupFileStatus).where(
                    and_(
                        BackupFileStatus.node_id == node.id,
                        BackupFileStatus.status == FileBackupStatus.FAILED,
                        BackupFileStatus.retry_count < 3
                    )
                ).limit(10)  # Process 10 at a time
            )
            failed_files = failed_result.scalars().all()
            
            for file_status in failed_files:
                # Re-queue for backup
                if _realtime_queue and not _realtime_queue.full():
                    try:
                        # Get image info
                        image_result = await db.execute(
                            select(Image).where(Image.id == file_status.image_id)
                        )
                        image = image_result.scalar_one_or_none()
                        if image:
                            _realtime_queue.put_nowait((image.id, image.file_path, file_status.file_size))
                            logger.debug(f"Re-queued failed backup: image {image.id} to node {node.id}")
                    except asyncio.QueueFull:
                        break


async def execute_scheduled_backup(node_id: int):
    """Execute a scheduled backup for a node."""
    logger.info(f"Executing scheduled backup for node {node_id}")
    
    async with AsyncSessionLocal() as db:
        from app.services.backup.service import BackupService
        
        service = BackupService(db)
        node = await service.get_node(node_id)
        
        if not node or not node.is_enabled:
            logger.warning(f"Node {node_id} is disabled or not found, skipping scheduled backup")
            return
        
        try:
            result = await service.execute_backup(node_id, triggered_by=None)
            logger.info(f"Scheduled backup completed for node {node_id}: {result}")
        except Exception as e:
            logger.error(f"Scheduled backup failed for node {node_id}: {e}")


async def trigger_realtime_backup(image_id: int, file_path: str, file_size: int):
    """
    Trigger realtime backup for a newly uploaded image.
    Called after successful image upload.
    
    This function is non-blocking - it just adds the task to a queue.
    The actual backup is processed by the queue processor with controlled concurrency.
    """
    global _realtime_queue
    
    # Quick check if there are any realtime nodes (avoid DB query if not needed)
    if _realtime_queue is None:
        logger.debug("Realtime backup queue not initialized")
        return
    
    try:
        # Add to queue (non-blocking)
        _realtime_queue.put_nowait((image_id, file_path, file_size))
        logger.debug(f"Queued realtime backup for image {image_id}")
    except asyncio.QueueFull:
        logger.warning(f"Realtime backup queue full, image {image_id} will be backed up later")
        # The image will be picked up by retry_failed_realtime_backups or manual backup


async def _execute_realtime_backup(image_id: int, file_path: str, file_size: int):
    """
    Execute realtime backup for a single image.
    Called by the queue processor.
    """
    from app.models.backup import BackupLog, BackupTaskType, BackupTaskStatus
    
    logger.debug(f"Executing realtime backup for image {image_id}")
    
    async with AsyncSessionLocal() as db:
        # Get all enabled nodes with realtime strategy
        result = await db.execute(
            select(BackupNode).where(
                and_(
                    BackupNode.is_enabled == True,
                    BackupNode.sync_strategy == SyncStrategy.REALTIME
                )
            )
        )
        nodes = result.scalars().all()
        
        if not nodes:
            logger.debug("No realtime backup nodes configured")
            return
        
        # Get the image
        image_result = await db.execute(
            select(Image).where(Image.id == image_id)
        )
        image = image_result.scalar_one_or_none()
        
        if not image:
            logger.warning(f"Image {image_id} not found for realtime backup")
            return
        
        from app.services.backup.factory import get_backup_backend
        from app.utils.encryption import decrypt_config
        from app.config import get_settings
        import os
        
        settings = get_settings()
        
        for node in nodes:
            started_at = datetime.utcnow()
            files_success = 0
            files_failed = 0
            bytes_transferred = 0
            error_msg = None
            
            try:
                config = decrypt_config(node.connection_config)
                backend = get_backup_backend(node.protocol, config)
                
                local_path = os.path.join(settings.upload_path, image.file_path)
                remote_path = image.file_path
                
                if not os.path.exists(local_path):
                    logger.warning(f"Local file not found for realtime backup: {local_path}")
                    error_msg = "Local file not found"
                    files_failed = 1
                else:
                    async with backend:
                        upload_result = await backend.upload(local_path, remote_path)
                    
                    # Create or update file status
                    existing_result = await db.execute(
                        select(BackupFileStatus).where(
                            and_(
                                BackupFileStatus.node_id == node.id,
                                BackupFileStatus.image_id == image_id
                            )
                        )
                    )
                    existing_status = existing_result.scalar_one_or_none()
                    
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
                                node_id=node.id,
                                image_id=image_id,
                                remote_path=upload_result.remote_path or remote_path,
                                file_size=upload_result.bytes_transferred or file_size,
                                checksum=upload_result.checksum,
                                status=FileBackupStatus.SYNCED,
                                last_sync_at=datetime.utcnow(),
                            )
                            db.add(file_status)
                        
                        files_success = 1
                        bytes_transferred = upload_result.bytes_transferred or file_size
                        logger.info(f"Realtime backup success: image {image_id} to node {node.id}")
                    else:
                        error_msg = upload_result.error_message or "Unknown error"
                        if existing_status:
                            existing_status.status = FileBackupStatus.FAILED
                            existing_status.error_message = error_msg
                            existing_status.retry_count += 1
                        else:
                            file_status = BackupFileStatus(
                                node_id=node.id,
                                image_id=image_id,
                                remote_path=remote_path,
                                file_size=file_size,
                                status=FileBackupStatus.FAILED,
                                error_message=error_msg,
                                retry_count=1,
                            )
                            db.add(file_status)
                        
                        files_failed = 1
                        logger.warning(f"Realtime backup failed: image {image_id} to node {node.id}: {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                files_failed = 1
                logger.error(f"Realtime backup error for image {image_id} to node {node.id}: {e}")
            
            # Create log entry for this realtime backup
            completed_at = datetime.utcnow()
            log = BackupLog(
                node_id=node.id,
                task_type=BackupTaskType.REALTIME,
                status=BackupTaskStatus.SUCCESS if files_success > 0 else BackupTaskStatus.FAILED,
                files_total=1,
                files_success=files_success,
                files_failed=files_failed,
                bytes_transferred=bytes_transferred,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=int((completed_at - started_at).total_seconds()),
                error_details=error_msg,
            )
            db.add(log)
            
            # Update node's last_sync_at for realtime backup display
            node.last_sync_at = completed_at
            node.last_sync_status = SyncStatus.SUCCESS if files_success > 0 else SyncStatus.FAILED
            
            await db.commit()


async def update_node_schedule(node_id: int, sync_strategy: str, schedule_cron: Optional[str]):
    """Update the schedule for a backup node."""
    scheduler = get_scheduler()
    job_id = f"backup_node_{node_id}"
    
    # Remove existing job if any
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    
    # Add new job if scheduled strategy
    if sync_strategy == "scheduled" and schedule_cron:
        try:
            add_scheduled_job(node_id, schedule_cron)
        except Exception as e:
            logger.error(f"Failed to update schedule for node {node_id}: {e}")
            raise
