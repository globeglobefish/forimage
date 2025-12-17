from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.api.deps import get_admin_user

router = APIRouter(prefix="/audit-logs")


class AuditLogResponse(BaseModel):
    id: int
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    user_id: Optional[int]
    ip_address: str
    user_agent: Optional[str]
    details: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with filtering."""
    query = select(AuditLog)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # Paginate
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/actions")
async def get_action_types(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of distinct action types."""
    result = await db.execute(
        select(AuditLog.action).distinct()
    )
    actions = [row[0] for row in result.all()]
    
    return {"actions": actions}


@router.get("/resource-types")
async def get_resource_types(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of distinct resource types."""
    result = await db.execute(
        select(AuditLog.resource_type).distinct().where(AuditLog.resource_type.isnot(None))
    )
    types = [row[0] for row in result.all()]
    
    return {"resource_types": types}


async def create_audit_log(
    db: AsyncSession,
    action: str,
    ip_address: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    user_agent: Optional[str] = None,
    details: Optional[str] = None,
    log_status: str = "success",
):
    """Helper function to create audit log entries."""
    log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        status=log_status,
    )
    db.add(log)
    await db.commit()
    return log
