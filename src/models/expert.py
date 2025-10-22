"""Expert and reputation models for community-driven content curation."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ExpertStatus(str, Enum):
    """Expert status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_REVIEW = "pending_review"


class ExpertLevel(str, Enum):
    """Expert levels based on reputation."""
    NOVICE = "novice"         # 0-100 points
    CONTRIBUTOR = "contributor"  # 100-500 points
    EXPERT = "expert"        # 500-2000 points
    AUTHORITY = "authority"   # 2000-10000 points
    MASTER = "master"        # 10000+ points


class ReputationEventType(str, Enum):
    """Types of reputation events."""
    CONTENT_APPROVAL = "content_approval"
    CONTENT_REJECTION = "content_rejection"
    HELPFUL_FEEDBACK = "helpful_feedback"
    UNHELPFUL_FEEDBACK = "unhelpful_feedback"
    SOURCE_RECOMMENDATION = "source_recommendation"
    EXPERT_ENDORSEMENT = "expert_endorsement"
    COMMUNITY_AWARD = "community_award"
    MODERATION_ACTION = "moderation_action"
    QUALITY_CONTRIBUTION = "quality_contribution"
    SPAM_PENALTY = "spam_penalty"


class Expert(Base):
    """Expert model for community-driven content curation."""
    
    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    
    # Identity (may or may not be linked to a user account)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True)
    
    # Public profile
    display_name = Column(String(255), nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    # Expertise areas
    expertise_domains = Column(JSON, nullable=False, default=[])  # List of domain tags
    specializations = Column(JSON, nullable=False, default=[])   # Specific specializations
    languages = Column(JSON, nullable=False, default=["en"])      # Languages of expertise
    
    # Professional background
    title = Column(String(200))
    organization = Column(String(200))
    years_experience = Column(Integer)
    education = Column(JSON, nullable=False, default=[])
    certifications = Column(JSON, nullable=False, default=[])
    
    # Status and verification
    status = Column(String(50), nullable=False, default=ExpertStatus.ACTIVE.value)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_method = Column(String(100))  # email, linkedin, manual, etc.
    verified_at = Column(String(50))  # ISO timestamp
    verified_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    
    # Reputation system
    reputation_score = Column(Integer, nullable=False, default=0)
    expert_level = Column(String(50), nullable=False, default=ExpertLevel.NOVICE.value)
    
    # Activity metrics
    contributions_count = Column(Integer, nullable=False, default=0)
    endorsements_received = Column(Integer, nullable=False, default=0)
    endorsements_given = Column(Integer, nullable=False, default=0)
    helpful_votes = Column(Integer, nullable=False, default=0)
    unhelpful_votes = Column(Integer, nullable=False, default=0)
    
    # Content curation
    sources_recommended = Column(Integer, nullable=False, default=0)
    sources_approved = Column(Integer, nullable=False, default=0)
    content_reviewed = Column(Integer, nullable=False, default=0)
    
    # Contact and social
    website_url = Column(String(500))
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))
    email_hash = Column(String(255))  # Hashed for privacy
    
    # Availability and preferences
    available_for_questions = Column(Boolean, nullable=False, default=True)
    response_time_hours = Column(Integer, nullable=False, default=24)
    preferred_topics = Column(JSON, nullable=False, default=[])
    
    # Trust and quality metrics
    trust_score = Column(Float, nullable=False, default=0.5)  # 0-1
    accuracy_rate = Column(Float, nullable=False, default=0.0)  # Based on feedback
    response_quality_avg = Column(Float, nullable=False, default=0.0)  # Average quality score
    
    # Activity patterns
    last_active_at = Column(String(50))  # ISO timestamp
    avg_response_time_hours = Column(Float, nullable=False, default=24.0)
    active_hours = Column(JSON, nullable=False, default=[])  # Hours when typically active
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Moderation and compliance
    warning_count = Column(Integer, nullable=False, default=0)
    suspension_count = Column(Integer, nullable=False, default=0)
    last_warning_at = Column(String(50))  # ISO timestamp
    
    # Relationships
    tenant = relationship("Tenant", back_populates="experts")
    user = relationship("User", foreign_keys=[user_id])
    verified_by_user = relationship("User", foreign_keys=[verified_by])
    reputation_events = relationship("ReputationEvent", back_populates="expert", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Expert(display_name={self.display_name}, level={self.expert_level}, reputation={self.reputation_score})>"
    
    @property
    def is_active(self) -> bool:
        """Check if expert is active."""
        return self.status == ExpertStatus.ACTIVE.value
    
    @property
    def helpfulness_ratio(self) -> float:
        """Calculate helpfulness ratio from votes."""
        total_votes = self.helpful_votes + self.unhelpful_votes
        if total_votes == 0:
            return 0.5
        return self.helpful_votes / total_votes
    
    @property
    def is_high_reputation(self) -> bool:
        """Check if expert has high reputation."""
        return self.expert_level in [ExpertLevel.AUTHORITY.value, ExpertLevel.MASTER.value]
    
    def update_reputation(self, delta: int, event_type: str, notes: str = None):
        """Update reputation score and create reputation event."""
        old_score = self.reputation_score
        old_level = self.expert_level
        
        self.reputation_score = max(0, self.reputation_score + delta)
        
        # Update expert level based on new score
        if self.reputation_score >= 10000:
            self.expert_level = ExpertLevel.MASTER.value
        elif self.reputation_score >= 2000:
            self.expert_level = ExpertLevel.AUTHORITY.value
        elif self.reputation_score >= 500:
            self.expert_level = ExpertLevel.EXPERT.value
        elif self.reputation_score >= 100:
            self.expert_level = ExpertLevel.CONTRIBUTOR.value
        else:
            self.expert_level = ExpertLevel.NOVICE.value
        
        # Create reputation event
        from datetime import datetime
        
        reputation_event = ReputationEvent(
            expert_id=self.id,
            event_type=event_type,
            delta=delta,
            old_score=old_score,
            new_score=self.reputation_score,
            old_level=old_level,
            new_level=self.expert_level,
            notes=notes
        )
        
        return reputation_event
    
    def add_endorsement(self, from_expert_id: UUID = None):
        """Add an endorsement from another expert."""
        self.endorsements_received += 1
        
        # Endorsements from higher-level experts are worth more
        if from_expert_id:
            # This would need to query the endorsing expert's level
            reputation_boost = 10  # Base boost, could be adjusted based on endorser level
        else:
            reputation_boost = 5  # Regular endorsement
        
        return self.update_reputation(
            reputation_boost, 
            ReputationEventType.EXPERT_ENDORSEMENT.value,
            f"Endorsement received"
        )
    
    def record_helpful_vote(self, helpful: bool):
        """Record a helpful/unhelpful vote."""
        if helpful:
            self.helpful_votes += 1
            reputation_event = self.update_reputation(
                2, 
                ReputationEventType.HELPFUL_FEEDBACK.value,
                "Received helpful vote"
            )
        else:
            self.unhelpful_votes += 1
            reputation_event = self.update_reputation(
                -1, 
                ReputationEventType.UNHELPFUL_FEEDBACK.value,
                "Received unhelpful vote"
            )
        
        # Update trust score based on helpfulness ratio
        self.trust_score = min(1.0, max(0.0, self.helpfulness_ratio))
        
        return reputation_event
    
    def record_content_contribution(self, approved: bool, quality_score: float = None):
        """Record a content contribution."""
        self.contributions_count += 1
        
        if approved:
            self.sources_approved += 1
            reputation_delta = 5
            event_type = ReputationEventType.CONTENT_APPROVAL.value
            notes = "Content contribution approved"
            
            if quality_score and quality_score > 0.8:
                reputation_delta += 3
                event_type = ReputationEventType.QUALITY_CONTRIBUTION.value
                notes = f"High-quality content contribution (score: {quality_score:.2f})"
        else:
            reputation_delta = -2
            event_type = ReputationEventType.CONTENT_REJECTION.value
            notes = "Content contribution rejected"
        
        # Update accuracy rate
        total_approved = self.sources_approved
        total_contributions = self.contributions_count
        self.accuracy_rate = total_approved / total_contributions if total_contributions > 0 else 0.0
        
        return self.update_reputation(reputation_delta, event_type, notes)
    
    def has_expertise_in(self, domain: str) -> bool:
        """Check if expert has expertise in a domain."""
        return domain.lower() in [d.lower() for d in self.expertise_domains]
    
    def can_review_content(self, topic: str = None, language: str = None) -> bool:
        """Check if expert can review content in a topic/language."""
        if not self.is_active:
            return False
        
        if topic and not self.has_expertise_in(topic):
            return False
        
        if language and language not in self.languages:
            return False
        
        # Minimum reputation required for content review
        return self.reputation_score >= 100
    
    def get_weight_for_domain(self, domain: str) -> float:
        """Get expert's weight/authority for a specific domain."""
        if not self.has_expertise_in(domain):
            return 0.0
        
        # Base weight from expert level
        level_weights = {
            ExpertLevel.NOVICE.value: 0.2,
            ExpertLevel.CONTRIBUTOR.value: 0.4,
            ExpertLevel.EXPERT.value: 0.7,
            ExpertLevel.AUTHORITY.value: 0.9,
            ExpertLevel.MASTER.value: 1.0
        }
        
        base_weight = level_weights.get(self.expert_level, 0.2)
        
        # Adjust based on trust score and accuracy
        trust_factor = self.trust_score
        accuracy_factor = min(1.0, self.accuracy_rate + 0.2)  # Slight boost for accuracy
        
        return base_weight * trust_factor * accuracy_factor


class ReputationEvent(Base):
    """Track reputation changes for experts."""
    
    # Expert relationship
    expert_id = Column(UUID(as_uuid=True), ForeignKey("expert.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    delta = Column(Integer, nullable=False)  # Reputation change (+/-)
    
    # Score tracking
    old_score = Column(Integer, nullable=False)
    new_score = Column(Integer, nullable=False)
    
    # Level tracking
    old_level = Column(String(50), nullable=False)
    new_level = Column(String(50), nullable=False)
    
    # Context
    notes = Column(Text)
    related_content_id = Column(UUID(as_uuid=True), nullable=True)  # Related content/answer/etc
    awarded_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    
    # Relationships
    expert = relationship("Expert", back_populates="reputation_events")
    awarded_by_user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_reputation_expert_type', 'expert_id', 'event_type'),
        Index('idx_reputation_created_at', 'created_at'),
        Index('idx_reputation_delta', 'delta'),
    )
    
    def __repr__(self) -> str:
        return f"<ReputationEvent(expert_id={self.expert_id}, type={self.event_type}, delta={self.delta})>"
    
    @property
    def is_positive(self) -> bool:
        """Check if this is a positive reputation event."""
        return self.delta > 0
    
    @property
    def is_level_change(self) -> bool:
        """Check if this event caused a level change."""
        return self.old_level != self.new_level
    
    @property
    def level_change_direction(self) -> Optional[str]:
        """Get direction of level change."""
        if not self.is_level_change:
            return None
        
        level_order = [
            ExpertLevel.NOVICE.value,
            ExpertLevel.CONTRIBUTOR.value,
            ExpertLevel.EXPERT.value,
            ExpertLevel.AUTHORITY.value,
            ExpertLevel.MASTER.value
        ]
        
        try:
            old_idx = level_order.index(self.old_level)
            new_idx = level_order.index(self.new_level)
            
            if new_idx > old_idx:
                return "promotion"
            elif new_idx < old_idx:
                return "demotion"
        except ValueError:
            pass
        
        return None