"""Document model for ingested content."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Interval
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    """Document types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    PPTX = "pptx"
    PPT = "ppt"
    XLSX = "xlsx"
    XLS = "xls"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    XML = "xml"
    JSON = "json"
    CSV = "csv"
    RTF = "rtf"
    ODT = "odt"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    OTHER = "other"


class Document(Base):
    """Document model for ingested content."""
    
    # Tenant and source relationships
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("source.id"), nullable=False, index=True)
    
    # External identifiers
    external_id = Column(String(500), nullable=True, index=True)  # ID from source system
    url = Column(Text)  # Original URL if applicable
    file_path = Column(Text)  # Path in object storage
    
    # Basic metadata
    title = Column(String(1000), nullable=False, index=True)
    description = Column(Text)
    content_type = Column(String(100), nullable=False, default=DocumentType.OTHER.value)
    mime_type = Column(String(100))
    
    # Content information
    language = Column(String(10), nullable=False, default="en", index=True)
    encoding = Column(String(50), nullable=False, default="utf-8")
    size_bytes = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)
    word_count = Column(Integer, nullable=False, default=0)
    
    # Processing status
    status = Column(String(50), nullable=False, default=DocumentStatus.PENDING.value, index=True)
    processing_started_at = Column(String(50))  # ISO timestamp
    processing_completed_at = Column(String(50))  # ISO timestamp
    processing_duration_seconds = Column(Float)
    
    # Versioning
    version = Column(Integer, nullable=False, default=1)
    hash_md5 = Column(String(32), index=True)
    hash_sha256 = Column(String(64), index=True)
    
    # Content freshness and TTL
    published_at = Column(String(50))  # ISO timestamp of original publication
    modified_at = Column(String(50))  # ISO timestamp of last modification
    ttl = Column(Interval)  # Time to live
    expires_at = Column(String(50))  # ISO timestamp when document expires
    
    # Quality and trust scores
    quality_score = Column(Float, nullable=False, default=0.8)  # 0.0 to 1.0
    relevance_score = Column(Float, nullable=False, default=0.8)  # 0.0 to 1.0
    trust_score = Column(Float, nullable=False, default=0.8)  # Inherited from source
    
    # Author and attribution
    author = Column(String(500))
    author_email = Column(String(255))
    organization = Column(String(500))
    copyright_info = Column(Text)
    
    # Content structure
    has_images = Column(String(10), nullable=False, default="false")  # Boolean as string
    has_tables = Column(String(10), nullable=False, default="false")  # Boolean as string
    has_links = Column(String(10), nullable=False, default="false")  # Boolean as string
    has_code = Column(String(10), nullable=False, default="false")  # Boolean as string
    
    # Extraction results
    text_content = Column(Text)  # Full extracted text
    summary = Column(Text)  # AI-generated summary
    keywords = Column(JSON, nullable=False, default=[])
    entities = Column(JSON, nullable=False, default=[])  # Named entities
    topics = Column(JSON, nullable=False, default=[])  # Topic classifications
    
    # Processing configuration used
    chunk_size = Column(Integer, nullable=False, default=600)
    chunk_overlap = Column(Integer, nullable=False, default=100)
    embedding_model = Column(String(100), nullable=False, default="text-embedding-3-large")
    
    # Statistics
    chunk_count = Column(Integer, nullable=False, default=0)
    embedding_count = Column(Integer, nullable=False, default=0)
    retrieval_count = Column(Integer, nullable=False, default=0)  # How many times retrieved
    
    # Metadata and tags
    tags = Column(JSON, nullable=False, default=[])
    categories = Column(JSON, nullable=False, default=[])
    extra_metadata = Column(JSON, nullable=False, default={})
    
    # Error tracking
    last_error = Column(Text)
    last_error_at = Column(String(50))  # ISO timestamp
    error_count = Column(Integer, nullable=False, default=0)
    
    # Privacy and compliance
    contains_pii = Column(String(10), nullable=False, default="false")  # Boolean as string
    pii_categories = Column(JSON, nullable=False, default=[])
    is_public = Column(String(10), nullable=False, default="true")  # Boolean as string
    access_level = Column(String(50), nullable=False, default="tenant")  # tenant, user, public
    
    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    source = relationship("Source", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(title={self.title[:50]}, status={self.status})>"
    
    @property
    def is_processed(self) -> bool:
        """Check if document is fully processed."""
        return self.status == DocumentStatus.PROCESSED.value
    
    @property
    def is_expired(self) -> bool:
        """Check if document has expired based on TTL."""
        if not self.expires_at:
            return False
        
        from datetime import datetime
        try:
            expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow().replace(tzinfo=expires.tzinfo) > expires
        except:
            return False
    
    @property
    def freshness_score(self) -> float:
        """Calculate freshness score based on age and TTL."""
        if not self.ttl or not self.created_at:
            return 1.0
        
        from datetime import datetime, timedelta
        
        try:
            age = datetime.utcnow() - self.created_at.replace(tzinfo=None)
            ttl_seconds = self.ttl.total_seconds()
            
            if age.total_seconds() > ttl_seconds:
                return 0.0
            
            # Linear decay from 1.0 to 0.1 over TTL period
            decay_factor = age.total_seconds() / ttl_seconds
            return max(0.1, 1.0 - decay_factor * 0.9)
        except:
            return 1.0
    
    @property
    def processing_time(self) -> Optional[float]:
        """Get processing duration in seconds."""
        return self.processing_duration_seconds
    
    def get_metadata(self, key: str, default=None):
        """Get metadata value by key."""
        return self.extra_metadata.get(key, default)
    
    def set_metadata(self, key: str, value):
        """Set metadata value."""
        if not self.extra_metadata:
            self.extra_metadata = {}
        self.extra_metadata[key] = value
    
    def add_tag(self, tag: str):
        """Add a tag to the document."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str):
        """Remove a tag from the document."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def mark_as_processed(self):
        """Mark document as successfully processed."""
        from datetime import datetime
        
        self.status = DocumentStatus.PROCESSED.value
        self.processing_completed_at = datetime.utcnow().isoformat() + "Z"
        
        if self.processing_started_at:
            try:
                started = datetime.fromisoformat(self.processing_started_at.replace('Z', '+00:00'))
                completed = datetime.utcnow().replace(tzinfo=started.tzinfo)
                self.processing_duration_seconds = (completed - started).total_seconds()
            except:
                pass
    
    def mark_as_failed(self, error: str):
        """Mark document as failed with error message."""
        from datetime import datetime
        
        self.status = DocumentStatus.FAILED.value
        self.last_error = error
        self.last_error_at = datetime.utcnow().isoformat() + "Z"
        self.error_count += 1