"""Reputation tracking models for expert system."""
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, JSON

from src.models.base import BaseModel


class ReputationEventType(str, Enum):
    """Types of reputation events."""
    CONTENT_CONTRIBUTION = "content_contribution"
    PEER_REVIEW_GIVEN = "peer_review_given"
    PEER_REVIEW_RECEIVED = "peer_review_received"
    USER_FEEDBACK_POSITIVE = "user_feedback_positive"
    USER_FEEDBACK_NEGATIVE = "user_feedback_negative"
    BADGE_EARNED = "badge_earned"
    EXPERT_ENDORSEMENT = "expert_endorsement"
    QUALITY_RECOGNITION = "quality_recognition"
    CONSISTENCY_BONUS = "consistency_bonus"
    PENALTY_APPLIED = "penalty_applied"


class Reputation(BaseModel):
    """Model for tracking user reputation scores."""
    
    __tablename__ = "reputations"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True, unique=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Overall reputation
    overall_score = Column(Float, default=0.0)
    reputation_level = Column(String, default="Novice")
    
    # Component scores
    content_quality_score = Column(Float, default=0.0)
    peer_review_score = Column(Float, default=0.0)
    user_feedback_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    domain_expertise_score = Column(Float, default=0.0)
    
    # Calculation metadata
    calculation_mode = Column(String, default="weighted")
    confidence = Column(Float, default=0.5)
    last_calculated = Column(String, nullable=True)
    
    # Historical tracking
    score_history = Column(JSON, default=[])  # Last 10 scores
    peak_score = Column(Float, default=0.0)
    peak_achieved_at = Column(String, nullable=True)
    
    # Domain-specific scores
    domain_scores = Column(JSON, default={})  # Domain -> score mapping
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def update_score(
        self,
        new_score: float,
        component_scores: dict,
        mode: str,
        confidence: float
    ):
        """Update reputation score and metadata."""
        from datetime import datetime
        
        # Update history
        if not self.score_history:
            self.score_history = []
        
        self.score_history.append({
            "score": self.overall_score,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Keep only last 10 entries
        if len(self.score_history) > 10:
            self.score_history = self.score_history[-10:]
        
        # Update scores
        self.overall_score = new_score
        self.content_quality_score = component_scores.get("content_quality", 0.0)
        self.peer_review_score = component_scores.get("peer_reviews", 0.0)
        self.user_feedback_score = component_scores.get("user_feedback", 0.0)
        self.consistency_score = component_scores.get("consistency", 0.0)
        self.domain_expertise_score = component_scores.get("domain_expertise", 0.0)
        
        # Update metadata
        self.calculation_mode = mode
        self.confidence = confidence
        self.last_calculated = datetime.utcnow().isoformat() + "Z"
        
        # Update peak if necessary
        if new_score > self.peak_score:
            self.peak_score = new_score
            self.peak_achieved_at = datetime.utcnow().isoformat() + "Z"
        
        # Update reputation level
        self.reputation_level = self._calculate_level(new_score)
    
    def _calculate_level(self, score: float) -> str:
        """Calculate reputation level from score."""
        if score >= 90:
            return "Master"
        elif score >= 80:
            return "Expert"
        elif score >= 70:
            return "Advanced"
        elif score >= 60:
            return "Intermediate"
        elif score >= 40:
            return "Beginner"
        else:
            return "Novice"


class ReputationEvent(BaseModel):
    """Model for tracking individual reputation events."""
    
    __tablename__ = "reputation_events"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Event details
    event_type = Column(String, nullable=False, index=True)
    impact_score = Column(Float, nullable=False)
    
    # Context
    content_id = Column(String, nullable=True, index=True)
    content_type = Column(String, nullable=True)
    
    # Description
    description = Column(String, nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)