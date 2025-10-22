"""Admin service for platform administration."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole, UserStatus
from src.models.audit_log import AuditLog, AuditEventType
from src.models.document import Document, DocumentStatus
from src.models.tenant import Tenant, TenantStatus
from src.core.logging import get_logger

logger = get_logger(__name__)


class AdminService:
    """Service for administrative operations."""

    async def get_platform_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get overall platform statistics."""

        # Count users
        total_users = await db.scalar(select(func.count(User.id)))
        active_users = await db.scalar(
            select(func.count(User.id)).where(User.is_active == True)
        )

        # Count documents
        total_documents = await db.scalar(select(func.count(Document.id)))
        active_documents = await db.scalar(
            select(func.count(Document.id)).where(
                Document.status == DocumentStatus.ACTIVE
            )
        )

        # Count tenants
        total_tenants = await db.scalar(select(func.count(Tenant.id)))
        active_tenants = await db.scalar(
            select(func.count(Tenant.id)).where(
                Tenant.status == TenantStatus.ACTIVE
            )
        )

        return {
            "users": {
                "total": total_users or 0,
                "active": active_users or 0,
            },
            "documents": {
                "total": total_documents or 0,
                "active": active_documents or 0,
            },
            "tenants": {
                "total": total_tenants or 0,
                "active": active_tenants or 0,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_recent_audit_logs(
        self,
        db: AsyncSession,
        limit: int = 100,
        event_type: Optional[AuditEventType] = None,
    ) -> List[AuditLog]:
        """Get recent audit logs."""

        query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)

        if event_type:
            query = query.where(AuditLog.event_type == event_type)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_activity(
        self,
        db: AsyncSession,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get user activity statistics."""

        since_date = datetime.utcnow() - timedelta(days=days)

        # Count audit logs for user
        audit_count = await db.scalar(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= since_date,
                )
            )
        )

        # Count documents created by user
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.created_by == user_id,
                    Document.created_at >= since_date,
                )
            )
        )

        return {
            "user_id": user_id,
            "period_days": days,
            "audit_events": audit_count or 0,
            "documents_created": doc_count or 0,
        }

    async def update_user_role(
        self,
        db: AsyncSession,
        user_id: str,
        new_role: UserRole,
        admin_user_id: str,
    ) -> User:
        """Update a user's role."""

        user = await db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()

        # Create audit log
        audit_log = AuditLog(
            user_id=admin_user_id,
            event_type=AuditEventType.USER_ROLE_CHANGED,
            resource_type="user",
            resource_id=user_id,
            details={
                "old_role": old_role.value,
                "new_role": new_role.value,
            },
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(user)

        logger.info(
            "User role updated",
            user_id=user_id,
            old_role=old_role,
            new_role=new_role,
            admin_user_id=admin_user_id,
        )

        return user

    async def deactivate_user(
        self,
        db: AsyncSession,
        user_id: str,
        admin_user_id: str,
        reason: Optional[str] = None,
    ) -> User:
        """Deactivate a user account."""

        user = await db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.is_active = False
        user.status = UserStatus.DISABLED
        user.updated_at = datetime.utcnow()

        # Create audit log
        audit_log = AuditLog(
            user_id=admin_user_id,
            event_type=AuditEventType.USER_DEACTIVATED,
            resource_type="user",
            resource_id=user_id,
            details={"reason": reason} if reason else {},
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(user)

        logger.warning(
            "User deactivated",
            user_id=user_id,
            admin_user_id=admin_user_id,
            reason=reason,
        )

        return user

    async def get_system_health(self, db: AsyncSession) -> Dict[str, Any]:
        """Get system health status."""

        # Simple database connectivity check
        try:
            await db.execute(select(1))
            db_status = "healthy"
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            db_status = "unhealthy"

        return {
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton instance
admin_service = AdminService()
