"""Feedback model for user feedback on answers and system performance."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class FeedbackSignal(str, Enum):
    """Types of feedback signals."""
    THUMBS_UP = "up"
    THUMBS_DOWN = "down"
    RATING = "rating"  # 1-5 stars
    PAIRWISE = "pairwise"  # A vs B comparison
    EDIT = "edit"  # User suggested edit
    CORRECTION = "correction"  # Factual correction
    REPORT = "report"  # Report inappropriate content


class FeedbackReason(str, Enum):
    """Reasons for negative feedback."""
    IRRELEVANT = "irrelevant"
    OUTDATED = "outdated"
    HALLUCINATION = "hallucination"
    FACTUAL_ERROR = "factual_error"
    POOR_STYLE = "poor_style"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    INAPPROPRIATE = "inappropriate"
    MISSING_CONTEXT = "missing_context"
    WRONG_LANGUAGE = "wrong_language"
    TECHNICAL_ERROR = "technical_error"
    BIAS = "bias"
    UNCLEAR = "unclear"
    INCOMPLETE = "incomplete"


class FeedbackStatus(str, Enum):
    """Feedback processing status."""
    PENDING = "pending"
    PROCESSED = "processed"
    APPLIED = "applied"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class Feedback(Base):
    """User feedback on answers and system performance."""
    
    # Context
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answer.id"), nullable=False, index=True)
    
    # Query context
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Feedback signal
    signal = Column(String(20), nullable=False, index=True)
    rating = Column(Float, nullable=True)  # 1-5 for rating feedback
    
    # Reasons and explanations
    reasons = Column(JSON, nullable=False, default=[])  # List of reason codes
    feedback_text = Column(Text)  # Free-form feedback
    suggested_fix = Column(Text)  # Suggested correction/improvement
    
    # Sources and citations feedback
    used_sources = Column(JSON, nullable=False, default=[])  # Sources used in answer
    source_quality_ratings = Column(JSON, nullable=False, default={})  # Source ID -> rating
    citation_feedback = Column(JSON, nullable=False, default=[])  # Citation-specific feedback
    
    # Model and routing feedback
    model_choice = Column(String(100), nullable=False)  # Model used for answer
    model_appropriateness = Column(Float, nullable=True)  # Was model choice appropriate?
    routing_feedback = Column(Text)  # Feedback on model routing decision
    
    # Performance feedback
    latency_ms = Column(Float, nullable=False)
    latency_acceptable = Column(Boolean, nullable=True)
    cost_awareness = Column(Boolean, nullable=False, default=False)  # User aware of cost
    
    # Comparison feedback (for pairwise)
    comparison_answer_id = Column(UUID(as_uuid=True), ForeignKey("answer.id"), nullable=True)
    preferred_answer = Column(String(10), nullable=True)  # "current", "comparison", "neither"
    comparison_reasons = Column(JSON, nullable=False, default=[])
    
    # Processing status
    status = Column(String(50), nullable=False, default=FeedbackStatus.PENDING.value, index=True)
    processed_at = Column(String(50))  # ISO timestamp
    applied_at = Column(String(50))  # ISO timestamp when improvements applied
    
    # Impact tracking
    weight = Column(Float, nullable=False, default=1.0)  # Weight for this feedback
    confidence = Column(Float, nullable=False, default=1.0)  # Confidence in feedback
    helpfulness_votes = Column(Integer, nullable=False, default=0)  # From other users
    
    # User context
    user_expertise_level = Column(String(50))  # User's expertise in the topic
    user_satisfaction_before = Column(Float, nullable=True)  # Before this answer
    user_satisfaction_after = Column(Float, nullable=True)  # After this answer
    
    # Device and context
    device_type = Column(String(50))  # mobile, desktop, tablet
    browser = Column(String(100))
    viewport_size = Column(String(20))  # e.g., "1920x1080"
    
    # Follow-up actions
    user_refined_query = Column(Text)  # Did user refine their query after?
    user_asked_followup = Column(Boolean, nullable=False, default=False)
    session_abandoned = Column(Boolean, nullable=False, default=False)
    
    # Moderation
    is_spam = Column(Boolean, nullable=False, default=False)
    is_abusive = Column(Boolean, nullable=False, default=False)
    moderation_notes = Column(Text)
    moderated_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", foreign_keys=[user_id], back_populates="feedback")
    answer = relationship("Answer", foreign_keys=[answer_id])
    comparison_answer = relationship("Answer", foreign_keys=[comparison_answer_id])
    moderated_by_user = relationship("User", foreign_keys=[moderated_by])
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_feedback_answer_signal', 'answer_id', 'signal'),
        Index('idx_feedback_user_created', 'user_id', 'created_at'),
        Index('idx_feedback_model_rating', 'model_choice', 'rating'),
        Index('idx_feedback_status_processed', 'status', 'processed_at'),
        Index('idx_feedback_query_session', 'query_id', 'session_id'),
    )
    
    def __repr__(self) -> str:
        return f"<Feedback(signal={self.signal}, rating={self.rating}, model={self.model_choice})>"
    
    @property
    def is_positive(self) -> bool:
        """Check if feedback is positive."""
        if self.signal == FeedbackSignal.THUMBS_UP.value:
            return True
        elif self.signal == FeedbackSignal.RATING.value and self.rating:
            return self.rating >= 3.0
        return False
    
    @property
    def is_negative(self) -> bool:
        """Check if feedback is negative."""
        if self.signal == FeedbackSignal.THUMBS_DOWN.value:
            return True
        elif self.signal == FeedbackSignal.RATING.value and self.rating:
            return self.rating < 3.0
        return False
    
    @property
    def has_actionable_feedback(self) -> bool:
        """Check if feedback contains actionable information."""
        return bool(
            self.feedback_text or 
            self.suggested_fix or 
            self.reasons or
            self.routing_feedback
        )
    
    @property
    def severity_score(self) -> float:
        """Calculate severity score for negative feedback."""
        if self.is_positive:
            return 0.0
        
        severity = 0.0
        
        # Base severity from signal
        if self.signal == FeedbackSignal.THUMBS_DOWN.value:
            severity += 0.3
        elif self.signal == FeedbackSignal.RATING.value and self.rating:
            severity += (3.0 - self.rating) / 2.0  # Scale 1-3 to 0-1
        
        # Additional severity from reasons
        high_severity_reasons = {
            FeedbackReason.HALLUCINATION.value: 0.4,
            FeedbackReason.FACTUAL_ERROR.value: 0.3,
            FeedbackReason.INAPPROPRIATE.value: 0.4,
            FeedbackReason.BIAS.value: 0.3
        }
        
        medium_severity_reasons = {
            FeedbackReason.OUTDATED.value: 0.2,
            FeedbackReason.IRRELEVANT.value: 0.2,
            FeedbackReason.MISSING_CONTEXT.value: 0.2,
            FeedbackReason.INCOMPLETE.value: 0.15
        }
        
        for reason in self.reasons:
            if reason in high_severity_reasons:
                severity += high_severity_reasons[reason]
            elif reason in medium_severity_reasons:
                severity += medium_severity_reasons[reason]
            else:
                severity += 0.1  # Low severity
        
        return min(1.0, severity)
    
    def add_reason(self, reason: str):
        """Add a feedback reason."""
        if not self.reasons:
            self.reasons = []
        
        if reason not in self.reasons:
            self.reasons.append(reason)
    
    def set_source_rating(self, source_id: str, rating: float):
        """Set rating for a specific source."""
        if not self.source_quality_ratings:
            self.source_quality_ratings = {}
        
        self.source_quality_ratings[source_id] = max(1.0, min(5.0, rating))
    
    def add_citation_feedback(self, citation_id: str, helpful: bool, note: str = None):
        """Add feedback for a specific citation."""
        if not self.citation_feedback:
            self.citation_feedback = []
        
        citation_fb = {
            "citation_id": citation_id,
            "helpful": helpful,
            "note": note
        }
        
        # Remove existing feedback for this citation
        self.citation_feedback = [
            fb for fb in self.citation_feedback 
            if fb.get("citation_id") != citation_id
        ]
        
        self.citation_feedback.append(citation_fb)
    
    def mark_as_processed(self, notes: str = None):
        """Mark feedback as processed."""
        from datetime import datetime
        
        self.status = FeedbackStatus.PROCESSED.value
        self.processed_at = datetime.utcnow().isoformat() + "Z"
        
        if notes and not self.feedback_text:
            self.feedback_text = notes
    
    def mark_as_applied(self, notes: str = None):
        """Mark feedback as applied to improve the system."""
        from datetime import datetime
        
        self.status = FeedbackStatus.APPLIED.value
        self.applied_at = datetime.utcnow().isoformat() + "Z"
        
        if notes:
            if self.feedback_text:
                self.feedback_text += f"\n\nApplication notes: {notes}"
            else:
                self.feedback_text = f"Application notes: {notes}"
    
    def calculate_weight(self) -> float:
        """Calculate weight for this feedback based on user and context."""
        weight = 1.0
        
        # User expertise boost
        expertise_multipliers = {
            "expert": 2.0,
            "advanced": 1.5,
            "intermediate": 1.2,
            "beginner": 1.0
        }
        
        if self.user_expertise_level:
            weight *= expertise_multipliers.get(self.user_expertise_level, 1.0)
        
        # Detailed feedback gets higher weight
        if self.has_actionable_feedback:
            weight *= 1.3
        
        # Consensus with other feedback
        if self.helpfulness_votes > 3:
            weight *= 1.2
        elif self.helpfulness_votes < -2:
            weight *= 0.5
        
        # Reduce weight for potential spam/abuse
        if self.is_spam or self.is_abusive:
            weight *= 0.1
        
        return min(3.0, max(0.1, weight))
    
    def get_improvement_suggestions(self) -> List[Dict]:
        """Extract actionable improvement suggestions."""
        suggestions = []
        
        # Model routing improvements
        if self.model_appropriateness and self.model_appropriateness < 0.5:
            suggestions.append({
                "type": "model_routing",
                "description": "Consider different model for this query type",
                "priority": "medium",
                "context": self.routing_feedback
            })
        
        # Content quality improvements
        if FeedbackReason.HALLUCINATION.value in self.reasons:
            suggestions.append({
                "type": "grounding",
                "description": "Improve grounding to source material",
                "priority": "high",
                "context": self.suggested_fix
            })
        
        if FeedbackReason.OUTDATED.value in self.reasons:
            suggestions.append({
                "type": "freshness",
                "description": "Use more recent sources",
                "priority": "medium",
                "context": None
            })
        
        # Source quality improvements
        poor_sources = [
            source_id for source_id, rating in self.source_quality_ratings.items()
            if rating < 3.0
        ]
        
        if poor_sources:
            suggestions.append({
                "type": "source_quality",
                "description": f"Improve quality of sources: {', '.join(poor_sources[:3])}",
                "priority": "medium",
                "context": f"Sources rated poorly: {poor_sources}"
            })
        
        return suggestions