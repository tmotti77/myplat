"""Contribution models for tracking user content submissions."""
from enum import Enum
from sqlalchemy import Column, String, Float, Integer, JSON

from src.models.base import BaseModel


class ContributionType(str, Enum):
    """Types of contributions."""
    DOCUMENT_UPLOAD = "document_upload"
    SOURCE_RECOMMENDATION = "source_recommendation"
    CONTENT_CREATION = "content_creation"
    ANSWER_SUBMISSION = "answer_submission"
    CITATION_ADDITION = "citation_addition"
    CORRECTION_SUBMISSION = "correction_submission"
    TRANSLATION = "translation"
    ANNOTATION = "annotation"


class ContributionStatus(str, Enum):
    """Status of contributions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Contribution(BaseModel):
    """Model for tracking user contributions."""
    
    __tablename__ = "contributions"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Contribution details
    contribution_type = Column(String, nullable=False, index=True)
    status = Column(String, default=ContributionStatus.PENDING.value)
    
    # Content reference
    content_id = Column(String, nullable=False, index=True)
    content_type = Column(String, nullable=False)
    
    # Quality metrics
    quality_score = Column(Float, default=0.5)
    user_rating = Column(Float, nullable=True)
    peer_review_score = Column(Float, nullable=True)
    
    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    
    # Review information
    reviewed_by = Column(String, nullable=True)
    review_notes = Column(String, nullable=True)
    reviewed_at = Column(String, nullable=True)
    
    # Domain and categorization
    domain = Column(String, nullable=True, index=True)
    tags = Column(JSON, default=[])
    language = Column(String, default="en")
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def approve(self, reviewed_by: str, notes: str = None):
        """Approve the contribution."""
        from datetime import datetime
        
        self.status = ContributionStatus.APPROVED.value
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow().isoformat() + "Z"
        if notes:
            self.review_notes = notes
    
    def reject(self, reviewed_by: str, notes: str = None):
        """Reject the contribution."""
        from datetime import datetime
        
        self.status = ContributionStatus.REJECTED.value
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow().isoformat() + "Z"
        if notes:
            self.review_notes = notes
    
    def publish(self):
        """Mark contribution as published."""
        self.status = ContributionStatus.PUBLISHED.value
    
    def update_engagement(self, views: int = 0, likes: int = 0, shares: int = 0, downloads: int = 0):
        """Update engagement metrics."""
        self.views += views
        self.likes += likes
        self.shares += shares
        self.downloads += downloads
    
    def calculate_impact_score(self) -> float:
        """Calculate impact score based on engagement and quality."""
        # Base score from quality
        impact = self.quality_score * 0.4
        
        # Engagement factors
        engagement_score = (
            self.views * 0.001 +
            self.likes * 0.01 +
            self.shares * 0.05 +
            self.downloads * 0.02
        )
        impact += min(0.3, engagement_score)  # Cap engagement contribution
        
        # Peer review factor
        if self.peer_review_score:
            impact += self.peer_review_score * 0.2
        
        # User rating factor
        if self.user_rating:
            rating_factor = (self.user_rating - 3.0) / 10.0  # Convert 1-5 to factor
            impact += rating_factor * 0.1
        
        return min(1.0, max(0.0, impact))
    
    @property
    def is_approved(self) -> bool:
        """Check if contribution is approved."""
        return self.status == ContributionStatus.APPROVED.value
    
    @property
    def is_published(self) -> bool:
        """Check if contribution is published."""
        return self.status == ContributionStatus.PUBLISHED.value