"""Admin management endpoints."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, func, desc, and_, or_
from pydantic import BaseModel, Field
import asyncio

from ..core.database import get_db
from ..core.auth import get_current_user, require_admin
from ..models.user import User, UserRole
from ..models.tenant import Tenant, TenantPlan
from ..models.document import Document, DocumentStatus
from ..models.conversation import Conversation
from ..models.message import Message
from ..models.audit_log import AuditLog, AuditEventType
from ..services.admin_service import AdminService
from ..services.analytics_service import AnalyticsService
from ..middleware.dependencies import get_admin_service, get_analytics_service

router = APIRouter()


class UserCreateRequest(BaseModel):
    email: str
    username: str
    full_name: str
    password: str
    role: UserRole = UserRole.USER
    tenant_id: Optional[str] = None
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    tenant_id: str
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class TenantCreateRequest(BaseModel):
    name: str
    domain: str
    plan: TenantPlan = TenantPlan.BASIC
    is_active: bool = True
    settings: Optional[Dict[str, Any]] = None


class TenantUpdateRequest(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    plan: Optional[TenantPlan] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    domain: str
    plan: TenantPlan
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_count: int
    document_count: int
    settings: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    users: Dict[str, int]
    tenants: Dict[str, int]
    documents: Dict[str, int]
    conversations: Dict[str, int]
    messages: Dict[str, int]
    storage: Dict[str, Union[int, float]]
    performance: Dict[str, Union[int, float]]


class AuditLogResponse(BaseModel):
    id: str
    event_type: AuditEventType
    event_action: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# User Management
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_filter: Optional[UserRole] = None,
    status_filter: Optional[bool] = None,
    tenant_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List users with filtering."""
    try:
        query = select(User)
        
        # Apply filters
        if role_filter:
            query = query.where(User.role == role_filter)
        
        if status_filter is not None:
            query = query.where(User.is_active == status_filter)
        
        if tenant_id:
            query = query.where(User.tenant_id == tenant_id)
        
        if search:
            query = query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        # Order and paginate
        query = query.order_by(desc(User.created_at))
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return [UserResponse.model_validate(user) for user in users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    admin_service: AdminService = Depends(get_admin_service)
):
    """Create a new user."""
    try:
        # Check if user exists
        existing_user = await db.execute(
            select(User).where(
                or_(
                    User.email == user_data.email,
                    User.username == user_data.username
                )
            )
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Create user
        user = await admin_service.create_user(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password=user_data.password,
            role=user_data.role,
            tenant_id=user_data.tenant_id,
            is_active=user_data.is_active
        )
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user details."""
    try:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user."""
    try:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user."""
    try:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Don't allow deleting the last admin
        if user.role == UserRole.ADMIN:
            admin_count = await db.execute(
                select(func.count(User.id)).where(User.role == UserRole.ADMIN)
            )
            if admin_count.scalar() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )
        
        await db.delete(user)
        await db.commit()
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


# Tenant Management
@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plan_filter: Optional[TenantPlan] = None,
    status_filter: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List tenants."""
    try:
        query = select(Tenant)
        
        if plan_filter:
            query = query.where(Tenant.plan == plan_filter)
        
        if status_filter is not None:
            query = query.where(Tenant.is_active == status_filter)
        
        # Order and paginate
        query = query.order_by(desc(Tenant.created_at))
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        tenants = result.scalars().all()
        
        # Get user and document counts for each tenant
        tenant_responses = []
        for tenant in tenants:
            user_count = await db.execute(
                select(func.count(User.id)).where(User.tenant_id == tenant.id)
            )
            document_count = await db.execute(
                select(func.count(Document.id)).where(Document.tenant_id == tenant.id)
            )
            
            tenant_data = TenantResponse.model_validate(tenant)
            tenant_data.user_count = user_count.scalar()
            tenant_data.document_count = document_count.scalar()
            tenant_responses.append(tenant_data)
        
        return tenant_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tenant."""
    try:
        # Check if tenant exists
        existing_tenant = await db.execute(
            select(Tenant).where(
                or_(
                    Tenant.name == tenant_data.name,
                    Tenant.domain == tenant_data.domain
                )
            )
        )
        if existing_tenant.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant with this name or domain already exists"
            )
        
        # Create tenant
        tenant = Tenant(
            name=tenant_data.name,
            domain=tenant_data.domain,
            plan=tenant_data.plan,
            is_active=tenant_data.is_active,
            settings=tenant_data.settings or {}
        )
        
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        
        tenant_response = TenantResponse.model_validate(tenant)
        tenant_response.user_count = 0
        tenant_response.document_count = 0
        
        return tenant_response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update tenant."""
    try:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(tenant, field, value)
        
        tenant.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(tenant)
        
        # Get counts
        user_count = await db.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant.id)
        )
        document_count = await db.execute(
            select(func.count(Document.id)).where(Document.tenant_id == tenant.id)
        )
        
        tenant_response = TenantResponse.model_validate(tenant)
        tenant_response.user_count = user_count.scalar()
        tenant_response.document_count = document_count.scalar()
        
        return tenant_response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


# System Statistics
@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get system-wide statistics."""
    try:
        # User stats
        user_stats = await db.execute(
            select([
                func.count(User.id).label('total'),
                func.count().filter(User.is_active == True).label('active'),
                func.count().filter(User.role == UserRole.ADMIN).label('admins'),
                func.count().filter(User.role == UserRole.USER).label('users')
            ])
        )
        user_data = user_stats.fetchone()
        
        # Tenant stats
        tenant_stats = await db.execute(
            select([
                func.count(Tenant.id).label('total'),
                func.count().filter(Tenant.is_active == True).label('active'),
                func.count().filter(Tenant.plan == TenantPlan.BASIC).label('basic'),
                func.count().filter(Tenant.plan == TenantPlan.PRO).label('pro'),
                func.count().filter(Tenant.plan == TenantPlan.ENTERPRISE).label('enterprise')
            ])
        )
        tenant_data = tenant_stats.fetchone()
        
        # Document stats
        doc_stats = await db.execute(
            select([
                func.count(Document.id).label('total'),
                func.count().filter(Document.status == DocumentStatus.PROCESSED).label('processed'),
                func.count().filter(Document.status == DocumentStatus.PROCESSING).label('processing'),
                func.count().filter(Document.status == DocumentStatus.FAILED).label('failed'),
                func.sum(Document.file_size).label('total_size')
            ])
        )
        doc_data = doc_stats.fetchone()
        
        # Conversation stats
        conv_stats = await db.execute(
            select([
                func.count(Conversation.id).label('total'),
                func.count(Message.id).label('total_messages')
            ]).outerjoin(Message, Conversation.id == Message.conversation_id)
        )
        conv_data = conv_stats.fetchone()
        
        # Performance stats (simplified)
        performance_stats = await analytics_service.get_performance_metrics()
        
        return SystemStatsResponse(
            users={
                "total": user_data.total or 0,
                "active": user_data.active or 0,
                "admins": user_data.admins or 0,
                "regular_users": user_data.users or 0
            },
            tenants={
                "total": tenant_data.total or 0,
                "active": tenant_data.active or 0,
                "basic": tenant_data.basic or 0,
                "pro": tenant_data.pro or 0,
                "enterprise": tenant_data.enterprise or 0
            },
            documents={
                "total": doc_data.total or 0,
                "processed": doc_data.processed or 0,
                "processing": doc_data.processing or 0,
                "failed": doc_data.failed or 0
            },
            conversations={
                "total": conv_data.total or 0
            },
            messages={
                "total": conv_data.total_messages or 0
            },
            storage={
                "total_size_gb": round((doc_data.total_size or 0) / (1024**3), 2),
                "avg_document_size_mb": round(
                    ((doc_data.total_size or 0) / (doc_data.total or 1)) / (1024**2), 2
                ) if doc_data.total > 0 else 0
            },
            performance=performance_stats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


# Audit Logs
@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action_filter: Optional[AuditEventType] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs."""
    try:
        query = select(AuditLog)
        
        # Apply filters
        if action_filter:
            query = query.where(AuditLog.event_type == action_filter)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if tenant_id:
            query = query.where(AuditLog.tenant_id == tenant_id)
        
        if date_from:
            query = query.where(AuditLog.created_at >= date_from)
        
        if date_to:
            query = query.where(AuditLog.created_at <= date_to)
        
        # Order and paginate
        query = query.order_by(desc(AuditLog.created_at))
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [AuditLogResponse.model_validate(log) for log in logs]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}"
        )


# System Maintenance
@router.post("/maintenance/cleanup")
async def cleanup_system(
    days: int = Query(30, ge=1, description="Delete data older than X days"),
    dry_run: bool = Query(True, description="Preview changes without applying"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    admin_service: AdminService = Depends(get_admin_service)
):
    """Clean up old system data."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cleanup_results = await admin_service.cleanup_old_data(
            cutoff_date=cutoff_date,
            dry_run=dry_run
        )
        
        return {
            "message": "Cleanup completed" if not dry_run else "Cleanup preview",
            "dry_run": dry_run,
            "cutoff_date": cutoff_date,
            "results": cleanup_results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.post("/maintenance/reindex")
async def reindex_system(
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    """Reindex all documents and embeddings."""
    try:
        # Start reindexing task
        task_id = await admin_service.start_reindex_task()
        
        return {
            "message": "Reindexing started",
            "task_id": task_id,
            "estimated_duration": "30-60 minutes"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {str(e)}"
        )


@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    """Get detailed system health information."""
    try:
        health_info = await admin_service.get_detailed_health()
        
        return health_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )