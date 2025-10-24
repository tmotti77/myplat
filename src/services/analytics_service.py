"""Analytics service for tracking and reporting."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog, AuditEventType
from src.models.document import Document
from src.models.user import User
from src.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics and reporting."""

    async def get_usage_stats(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics for a time period."""

        query_filters = [
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date,
        ]

        if tenant_id:
            # Filter by tenant if specified
            query_filters.append(AuditLog.tenant_id == tenant_id)

        # Count total events
        total_events = await db.scalar(
            select(func.count(AuditLog.id)).where(and_(*query_filters))
        )

        # Count unique users
        unique_users = await db.scalar(
            select(func.count(func.distinct(AuditLog.user_id))).where(
                and_(*query_filters)
            )
        )

        # Count events by type
        event_type_query = (
            select(
                AuditLog.event_type,
                func.count(AuditLog.id).label("count"),
            )
            .where(and_(*query_filters))
            .group_by(AuditLog.event_type)
        )

        event_type_result = await db.execute(event_type_query)
        events_by_type = {
            row.event_type.value: row.count for row in event_type_result.all()
        }

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_events": total_events or 0,
            "unique_users": unique_users or 0,
            "events_by_type": events_by_type,
        }

    async def get_document_stats(
        self,
        db: AsyncSession,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get document statistics."""

        query = select(Document)
        if tenant_id:
            query = query.where(Document.tenant_id == tenant_id)

        # Count total documents
        total_docs = await db.scalar(
            select(func.count(Document.id)).select_from(query.subquery())
        )

        # Count by type
        type_query = (
            select(
                Document.type,
                func.count(Document.id).label("count"),
            )
            .group_by(Document.type)
        )
        if tenant_id:
            type_query = type_query.where(Document.tenant_id == tenant_id)

        type_result = await db.execute(type_query)
        docs_by_type = {
            row.type.value: row.count for row in type_result.all()
        }

        # Count by status
        status_query = (
            select(
                Document.status,
                func.count(Document.id).label("count"),
            )
            .group_by(Document.status)
        )
        if tenant_id:
            status_query = status_query.where(Document.tenant_id == tenant_id)

        status_result = await db.execute(status_query)
        docs_by_status = {
            row.status.value: row.count for row in status_result.all()
        }

        return {
            "total_documents": total_docs or 0,
            "by_type": docs_by_type,
            "by_status": docs_by_status,
        }

    async def get_user_engagement(
        self,
        db: AsyncSession,
        days: int = 30,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get user engagement metrics."""

        since_date = datetime.utcnow() - timedelta(days=days)

        # Count active users (users who performed any action)
        active_users_query = select(func.count(func.distinct(AuditLog.user_id))).where(
            AuditLog.timestamp >= since_date
        )
        if tenant_id:
            active_users_query = active_users_query.where(
                AuditLog.tenant_id == tenant_id
            )

        active_users = await db.scalar(active_users_query)

        # Count total users
        total_users_query = select(func.count(User.id))
        if tenant_id:
            total_users_query = total_users_query.where(User.tenant_id == tenant_id)

        total_users = await db.scalar(total_users_query)

        # Calculate engagement rate
        engagement_rate = (
            (active_users / total_users * 100) if total_users and active_users else 0
        )

        return {
            "period_days": days,
            "total_users": total_users or 0,
            "active_users": active_users or 0,
            "engagement_rate": round(engagement_rate, 2),
        }

    async def get_search_analytics(
        self,
        db: AsyncSession,
        days: int = 30,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get search usage analytics."""

        since_date = datetime.utcnow() - timedelta(days=days)

        # Count search events
        search_filters = [
            AuditLog.timestamp >= since_date,
            AuditLog.event_type == AuditEventType.SEARCH_PERFORMED,
        ]
        if tenant_id:
            search_filters.append(AuditLog.tenant_id == tenant_id)

        total_searches = await db.scalar(
            select(func.count(AuditLog.id)).where(and_(*search_filters))
        )

        unique_searchers = await db.scalar(
            select(func.count(func.distinct(AuditLog.user_id))).where(
                and_(*search_filters)
            )
        )

        return {
            "period_days": days,
            "total_searches": total_searches or 0,
            "unique_searchers": unique_searchers or 0,
            "avg_searches_per_user": (
                round(total_searches / unique_searchers, 2)
                if unique_searchers and total_searches
                else 0
            ),
        }

    async def get_performance_metrics(
        self,
        db: AsyncSession,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get system performance metrics."""

        since_date = datetime.utcnow() - timedelta(days=days)

        # In a real implementation, this would fetch from a metrics store
        # For now, return placeholder data
        return {
            "period_days": days,
            "avg_response_time_ms": 0,
            "requests_per_second": 0,
            "error_rate": 0,
            "note": "Performance metrics require external monitoring integration",
        }


# Singleton instance
analytics_service = AnalyticsService()
