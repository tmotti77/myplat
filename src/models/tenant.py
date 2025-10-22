"""Tenant model for multi-tenancy support."""
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import relationship

from .base import Base


class TenantPlan(str, Enum):
    """Available tenant plans."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status options."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Tenant(Base):
    """Tenant model for multi-tenant architecture."""
    
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Plan and billing
    plan = Column(String(50), nullable=False, default=TenantPlan.BASIC.value)
    status = Column(String(50), nullable=False, default=TenantStatus.ACTIVE.value)
    
    # Region and localization
    region = Column(String(10), nullable=False, default="us-east-1")
    default_language = Column(String(10), nullable=False, default="en")
    supported_languages = Column(JSON, nullable=False, default=["en"])
    
    # Limits and quotas
    max_users = Column(Integer, nullable=False, default=10)
    max_documents = Column(Integer, nullable=False, default=10000)
    max_queries_per_day = Column(Integer, nullable=False, default=1000)
    max_storage_gb = Column(Integer, nullable=False, default=10)
    
    # Cost controls
    daily_cost_limit_usd = Column(Integer, nullable=False, default=100)  # Stored as cents
    monthly_cost_limit_usd = Column(Integer, nullable=False, default=3000)  # Stored as cents
    
    # Feature flags
    features = Column(JSON, nullable=False, default={
        "real_time_updates": True,
        "advanced_analytics": False,
        "expert_system": True,
        "feedback_learning": True,
        "cost_optimization": True,
        "custom_models": False,
        "api_access": True,
        "sso": False,
        "audit_logs": False,
        "priority_support": False
    })
    
    # Configuration
    config = Column(JSON, nullable=False, default={
        "chunk_size": 600,
        "chunk_overlap": 100,
        "embedding_model": "text-embedding-3-large",
        "default_llm_model": "gpt-4-turbo-preview",
        "retrieval_k": 20,
        "temperature": 0.1,
        "max_tokens": 4000
    })
    
    # Security and compliance
    encryption_enabled = Column(Boolean, nullable=False, default=True)
    audit_enabled = Column(Boolean, nullable=False, default=True)
    data_retention_days = Column(Integer, nullable=False, default=365)
    
    # Contact and billing info
    contact_email = Column(String(255), nullable=False)
    billing_email = Column(String(255))
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    experts = relationship("Expert", back_populates="tenant", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tenant(name={self.name}, plan={self.plan})>"
    
    @property
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE.value
    
    def has_feature(self, feature: str) -> bool:
        """Check if tenant has a specific feature enabled."""
        return self.features.get(feature, False)
    
    def get_config(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)