"""Source model for document sources and connectors."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class SourceKind(str, Enum):
    """Types of document sources."""
    URL = "url"
    RSS = "rss"
    API = "api"
    UPLOAD = "upload"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    DATABASE = "database"
    S3 = "s3"
    SHAREPOINT = "sharepoint"
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GITHUB = "github"
    GOOGLE_DRIVE = "google_drive"


class SourceStatus(str, Enum):
    """Source status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class CrawlFrequency(str, Enum):
    """Crawl frequency options."""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


class Source(Base):
    """Source model for document ingestion."""
    
    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Source configuration
    kind = Column(String(50), nullable=False, index=True)
    url = Column(Text)  # Primary URL or endpoint
    status = Column(String(50), nullable=False, default=SourceStatus.ACTIVE.value)
    
    # Authentication and access
    auth_config = Column(JSON, nullable=False, default={})  # Encrypted auth details
    headers = Column(JSON, nullable=False, default={})
    
    # Crawling and ingestion
    crawl_frequency = Column(String(50), nullable=False, default=CrawlFrequency.DAILY.value)
    last_crawl_at = Column(String(50))  # ISO timestamp
    next_crawl_at = Column(String(50))  # ISO timestamp
    crawl_count = Column(Integer, nullable=False, default=0)
    
    # Processing configuration
    parsing_config = Column(JSON, nullable=False, default={
        "extract_images": True,
        "extract_tables": True,
        "extract_links": True,
        "ocr_enabled": True,
        "languages": ["en", "he", "ar"],
        "chunk_size": 600,
        "chunk_overlap": 100
    })
    
    # Trust and quality
    trust_score = Column(Float, nullable=False, default=0.8)  # 0.0 to 1.0
    quality_score = Column(Float, nullable=False, default=0.8)  # Based on content quality
    
    # Content filtering
    include_patterns = Column(JSON, nullable=False, default=[])  # Regex patterns to include
    exclude_patterns = Column(JSON, nullable=False, default=[])  # Regex patterns to exclude
    allowed_domains = Column(JSON, nullable=False, default=[])
    blocked_domains = Column(JSON, nullable=False, default=[])
    
    # Metadata and tags
    tags = Column(JSON, nullable=False, default=[])
    categories = Column(JSON, nullable=False, default=[])
    source_extra_metadata = Column(JSON, nullable=False, default={})
    
    # Rate limiting and politeness
    rate_limit_requests_per_second = Column(Float, nullable=False, default=1.0)
    request_delay_seconds = Column(Float, nullable=False, default=1.0)
    user_agent = Column(String(500), nullable=False, default="RAG-Platform/1.0")
    
    # Monitoring and alerts
    health_check_enabled = Column(Boolean, nullable=False, default=True)
    health_check_interval_minutes = Column(Integer, nullable=False, default=60)
    alert_on_failure = Column(Boolean, nullable=False, default=True)
    alert_email = Column(String(255))
    
    # Statistics
    total_documents = Column(Integer, nullable=False, default=0)
    total_chunks = Column(Integer, nullable=False, default=0)
    total_size_bytes = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=1.0)
    
    # Error tracking
    last_error = Column(Text)
    last_error_at = Column(String(50))  # ISO timestamp
    error_count = Column(Integer, nullable=False, default=0)
    consecutive_errors = Column(Integer, nullable=False, default=0)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="sources")
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Source(name={self.name}, kind={self.kind})>"
    
    @property
    def is_active(self) -> bool:
        """Check if source is active."""
        return self.status == SourceStatus.ACTIVE.value
    
    @property
    def is_healthy(self) -> bool:
        """Check if source is healthy (no recent errors)."""
        return self.consecutive_errors < 5
    
    @property
    def needs_crawl(self) -> bool:
        """Check if source needs to be crawled."""
        if not self.is_active or self.crawl_frequency == CrawlFrequency.MANUAL.value:
            return False
        
        if not self.next_crawl_at:
            return True
            
        from datetime import datetime
        try:
            next_crawl = datetime.fromisoformat(self.next_crawl_at.replace('Z', '+00:00'))
            return datetime.utcnow().replace(tzinfo=next_crawl.tzinfo) >= next_crawl
        except:
            return True
    
    def get_auth_config(self, key: str, default=None):
        """Get authentication configuration value."""
        return self.auth_config.get(key, default)
    
    def get_parsing_config(self, key: str, default=None):
        """Get parsing configuration value."""
        return self.parsing_config.get(key, default)
    
    def update_stats(self, documents: int = 0, chunks: int = 0, size_bytes: int = 0, success: bool = True):
        """Update source statistics."""
        self.total_documents += documents
        self.total_chunks += chunks
        self.total_size_bytes += size_bytes
        
        if success:
            self.consecutive_errors = 0
            self.success_rate = min(1.0, self.success_rate + 0.01)
        else:
            self.error_count += 1
            self.consecutive_errors += 1
            self.success_rate = max(0.0, self.success_rate - 0.05)