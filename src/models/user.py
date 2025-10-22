"""User model with authentication and authorization."""
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    USER = "user"
    READONLY = "readonly"


class UserStatus(str, Enum):
    """User status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User model with multi-tenant support."""
    
    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    
    # Identity (hashed for privacy)
    email_hash = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=True, index=True)
    
    # Profile information
    display_name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    # Authentication
    auth_provider = Column(String(50), nullable=False, default="local")  # local, auth0, google, etc.
    auth_provider_id = Column(String(255), nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # For local auth
    
    # Authorization
    role = Column(String(50), nullable=False, default=UserRole.USER.value)
    permissions = Column(JSON, nullable=False, default=[])
    status = Column(String(50), nullable=False, default=UserStatus.ACTIVE.value)
    
    # Preferences and settings
    locale = Column(String(10), nullable=False, default="en")
    timezone = Column(String(50), nullable=False, default="UTC")
    theme = Column(String(20), nullable=False, default="light")
    
    # Email preferences
    email_notifications = Column(Boolean, nullable=False, default=True)
    digest_frequency = Column(String(20), nullable=False, default="weekly")  # daily, weekly, monthly, never
    
    # API access
    api_key_hash = Column(String(255), nullable=True, index=True)
    api_rate_limit = Column(JSON, nullable=False, default={
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    })
    
    # Session management
    last_login_at = Column(String(50))  # ISO timestamp
    last_activity_at = Column(String(50))  # ISO timestamp
    login_count = Column(String(10), nullable=False, default="0")
    
    # Terms and privacy
    terms_accepted_at = Column(String(50))  # ISO timestamp
    privacy_accepted_at = Column(String(50))  # ISO timestamp
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(display_name={self.display_name}, role={self.role})>"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE.value
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN.value
    
    @property
    def is_manager(self) -> bool:
        """Check if user is manager or admin."""
        return self.role in [UserRole.ADMIN.value, UserRole.MANAGER.value]
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        if self.is_admin:
            return True
        return permission in self.permissions
    
    def can_access_tenant(self, tenant_id: str) -> bool:
        """Check if user can access a specific tenant."""
        return str(self.tenant_id) == str(tenant_id)
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name