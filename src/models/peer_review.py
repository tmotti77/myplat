"""Peer review models for content quality assessment."""
from enum import Enum
from sqlalchemy import Column, String, Float, JSON

from src.models.base import BaseModel


class ReviewType(str, Enum):
    """Types of peer reviews."""
    QUALITY_REVIEW = "quality_review"
    ACCURACY_REVIEW = "accuracy_review"
    RELEVANCE_REVIEW = "relevance_review"
    COMPLETENESS_REVIEW = "completeness_review"
    CITATION_REVIEW = "citation_review"
    BIAS_REVIEW = "bias_review"
    EXPERT_VALIDATION = "expert_validation"


class ReviewStatus(str, Enum):
    """Status of peer reviews."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class PeerReview(BaseModel):
    """Model for peer reviews of content."""
    
    __tablename__ = "peer_reviews"
    
    # Core relationships
    reviewer_id = Column(String, nullable=False, index=True)
    content_id = Column(String, nullable=False, index=True)
    content_type = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Review details
    review_type = Column(String, nullable=False)
    status = Column(String, default=ReviewStatus.PENDING.value)
    
    # Scoring
    scores = Column(JSON, default={})  # Different aspect scores
    overall_score = Column(Float, nullable=True)
    
    # Qualitative feedback
    comments = Column(String, nullable=True)
    suggestions = Column(String, nullable=True)
    
    # Review quality metrics
    review_quality_score = Column(Float, nullable=True)
    helpfulness_votes = Column(String, default="0")
    
    # Timing
    time_spent_minutes = Column(Float, nullable=True)
    submitted_at = Column(String, nullable=True)
    
    # Validation
    validated_by = Column(String, nullable=True)
    validation_score = Column(Float, nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def submit(self):
        """Mark review as submitted."""
        from datetime import datetime
        
        self.status = ReviewStatus.SUBMITTED.value
        self.submitted_at = datetime.utcnow().isoformat() + "Z"
    
    def approve(self, approved_by: str):
        """Approve the review."""
        self.status = ReviewStatus.APPROVED.value
        self.validated_by = approved_by
    
    def reject(self, rejected_by: str, reason: str = None):
        """Reject the review."""
        self.status = ReviewStatus.REJECTED.value
        self.validated_by = rejected_by
        if reason:
            if not self.extra_metadata:
                self.extra_metadata = {}
            self.extra_metadata["rejection_reason"] = reason
    
    def calculate_overall_score(self):
        """Calculate overall score from component scores."""
        if not self.scores:
            return None
        
        # Simple average of all scores
        score_values = [v for v in self.scores.values() if isinstance(v, (int, float))]
        if score_values:
            self.overall_score = sum(score_values) / len(score_values)
        
        return self.overall_score
    
    @property
    def helpfulness_count(self) -> int:
        """Get helpfulness votes as integer."""
        return int(self.helpfulness_votes or "0")
    
    def add_helpfulness_vote(self):
        """Add a helpfulness vote."""
        current_count = self.helpfulness_count
        self.helpfulness_votes = str(current_count + 1)