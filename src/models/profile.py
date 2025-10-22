"""User profile model for personalization."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import Text as Vector

from sqlalchemy.orm import relationship

from .base import Base


class PreferenceType(str, Enum):
    """Types of user preferences."""
    CONTENT_DEPTH = "content_depth"  # brief, detailed, comprehensive
    RESPONSE_STYLE = "response_style"  # formal, casual, technical
    CITATION_STYLE = "citation_style"  # academic, journalistic, minimal
    LANGUAGE = "language"  # en, he, ar, etc.
    SOURCES = "sources"  # preferred source types
    TOPICS = "topics"  # preferred topics
    FORMAT = "format"  # text, bullet, table, etc.


class ContentDepth(str, Enum):
    """Content depth preferences."""
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class ResponseStyle(str, Enum):
    """Response style preferences."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    ACADEMIC = "academic"


class Profile(Base):
    """User profile for personalization and preferences."""
    
    # User relationship (one-to-one)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    
    # Basic preferences
    content_depth = Column(String(50), nullable=False, default=ContentDepth.STANDARD.value)
    response_style = Column(String(50), nullable=False, default=ResponseStyle.CONVERSATIONAL.value)
    preferred_language = Column(String(10), nullable=False, default="en")
    secondary_languages = Column(ARRAY(String), nullable=False, default=[])
    
    # Source preferences
    preferred_sources = Column(JSON, nullable=False, default=[])  # List of source IDs
    trusted_domains = Column(JSON, nullable=False, default=[])  # List of trusted domains
    blocked_sources = Column(JSON, nullable=False, default=[])  # List of blocked source IDs
    source_freshness_preference = Column(String(50), nullable=False, default="balanced")  # recent, balanced, comprehensive
    
    # Topic and domain preferences
    interested_topics = Column(JSON, nullable=False, default=[])  # Topics of interest
    expert_domains = Column(JSON, nullable=False, default=[])  # User's areas of expertise
    avoided_topics = Column(JSON, nullable=False, default=[])  # Topics to avoid
    
    # Response format preferences
    citation_style = Column(String(50), nullable=False, default="journalistic")
    max_response_length = Column(Integer, nullable=False, default=2000)  # Max tokens
    include_confidence_scores = Column(String(10), nullable=False, default="true")  # Boolean as string
    include_follow_up_questions = Column(String(10), nullable=False, default="true")  # Boolean as string
    
    # Personalization vectors
    user_embedding = Column(Vector, nullable=True)  # User interest embedding
    topic_preferences_vector = Column(Vector, nullable=True)  # Topic preference vector
    style_preferences_vector = Column(Vector, nullable=True)  # Style preference vector
    
    # Learning and adaptation
    interaction_count = Column(Integer, nullable=False, default=0)
    positive_feedback_count = Column(Integer, nullable=False, default=0)
    negative_feedback_count = Column(Integer, nullable=False, default=0)
    last_interaction_at = Column(String(50))  # ISO timestamp
    
    # Behavioral patterns
    avg_query_length = Column(Float, nullable=False, default=0.0)
    preferred_query_types = Column(JSON, nullable=False, default=[])  # factual, analytical, creative, etc.
    peak_usage_hours = Column(JSON, nullable=False, default=[])  # Hours of day when most active
    session_patterns = Column(JSON, nullable=False, default={})  # Session length, frequency, etc.
    
    # Expertise and context
    job_title = Column(String(200))
    industry = Column(String(100))
    education_level = Column(String(50))
    experience_years = Column(Integer)
    specializations = Column(JSON, nullable=False, default=[])
    
    # Accessibility and usability
    accessibility_needs = Column(JSON, nullable=False, default=[])
    ui_preferences = Column(JSON, nullable=False, default={
        "theme": "light",
        "font_size": "medium",
        "high_contrast": False,
        "reduced_motion": False,
        "screen_reader": False
    })
    
    # Privacy and data preferences
    data_sharing_consent = Column(String(10), nullable=False, default="false")  # Boolean as string
    analytics_opt_in = Column(String(10), nullable=False, default="true")  # Boolean as string
    personalization_opt_in = Column(String(10), nullable=False, default="true")  # Boolean as string
    
    # Advanced preferences
    advanced_settings = Column(JSON, nullable=False, default={
        "temperature": 0.1,
        "creativity_level": 0.3,
        "fact_checking_strictness": 0.8,
        "citation_density": "medium",
        "explanation_level": "standard"
    })
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    def __repr__(self) -> str:
        return f"<Profile(user_id={self.user_id}, style={self.response_style}, depth={self.content_depth})>"
    
    @property
    def is_personalization_enabled(self) -> bool:
        """Check if personalization is enabled."""
        return self.personalization_opt_in == "true"
    
    @property
    def feedback_ratio(self) -> float:
        """Calculate positive feedback ratio."""
        total = self.positive_feedback_count + self.negative_feedback_count
        if total == 0:
            return 0.5
        return self.positive_feedback_count / total
    
    @property
    def is_active_user(self) -> bool:
        """Check if user is active based on interaction patterns."""
        return self.interaction_count > 10 and self.feedback_ratio > 0.3
    
    def get_preference(self, key: str, default=None):
        """Get a preference value."""
        # Check advanced settings first
        if key in self.advanced_settings:
            return self.advanced_settings[key]
        
        # Check direct attributes
        if hasattr(self, key):
            return getattr(self, key)
        
        return default
    
    def set_preference(self, key: str, value):
        """Set a preference value."""
        # Update advanced settings
        if not self.advanced_settings:
            self.advanced_settings = {}
        self.advanced_settings[key] = value
    
    def add_trusted_domain(self, domain: str):
        """Add a trusted domain."""
        if not self.trusted_domains:
            self.trusted_domains = []
        
        if domain not in self.trusted_domains:
            self.trusted_domains.append(domain)
    
    def add_interested_topic(self, topic: str, weight: float = 1.0):
        """Add a topic of interest with weight."""
        if not self.interested_topics:
            self.interested_topics = []
        
        # Find existing topic
        for item in self.interested_topics:
            if isinstance(item, dict) and item.get("topic") == topic:
                item["weight"] = max(item.get("weight", 0), weight)
                return
        
        # Add new topic
        self.interested_topics.append({"topic": topic, "weight": weight})
    
    def update_interaction_stats(self, positive_feedback: bool = None):
        """Update interaction statistics."""
        from datetime import datetime
        
        self.interaction_count += 1
        self.last_interaction_at = datetime.utcnow().isoformat() + "Z"
        
        if positive_feedback is True:
            self.positive_feedback_count += 1
        elif positive_feedback is False:
            self.negative_feedback_count += 1
    
    def update_query_patterns(self, query_length: int, query_type: str = None):
        """Update query pattern analysis."""
        # Update average query length (exponential moving average)
        if self.avg_query_length == 0:
            self.avg_query_length = float(query_length)
        else:
            alpha = 0.1
            self.avg_query_length = alpha * query_length + (1 - alpha) * self.avg_query_length
        
        # Update preferred query types
        if query_type:
            if not self.preferred_query_types:
                self.preferred_query_types = []
            
            # Find existing type
            found = False
            for item in self.preferred_query_types:
                if isinstance(item, dict) and item.get("type") == query_type:
                    item["count"] = item.get("count", 0) + 1
                    found = True
                    break
            
            if not found:
                self.preferred_query_types.append({"type": query_type, "count": 1})
    
    def get_source_weight(self, source_id: str) -> float:
        """Get preference weight for a source."""
        # Check if explicitly preferred
        if source_id in self.preferred_sources:
            return 1.2
        
        # Check if blocked
        if source_id in self.blocked_sources:
            return 0.1
        
        # Default weight
        return 1.0
    
    def get_topic_interest(self, topic: str) -> float:
        """Get interest level for a topic."""
        if not self.interested_topics:
            return 0.5
        
        for item in self.interested_topics:
            if isinstance(item, dict) and item.get("topic") == topic:
                return item.get("weight", 1.0)
            elif isinstance(item, str) and item == topic:
                return 1.0
        
        # Check if topic is in avoided list
        if topic in self.avoided_topics:
            return 0.1
        
        return 0.5  # Neutral
    
    def should_include_confidence(self) -> bool:
        """Check if confidence scores should be included."""
        return self.include_confidence_scores == "true"
    
    def should_include_follow_ups(self) -> bool:
        """Check if follow-up questions should be included."""
        return self.include_follow_up_questions == "true"
    
    def get_max_tokens(self) -> int:
        """Get maximum response length in tokens."""
        depth_multipliers = {
            ContentDepth.BRIEF.value: 0.5,
            ContentDepth.STANDARD.value: 1.0,
            ContentDepth.DETAILED.value: 1.5,
            ContentDepth.COMPREHENSIVE.value: 2.0
        }
        
        multiplier = depth_multipliers.get(self.content_depth, 1.0)
        return int(self.max_response_length * multiplier)
    
    def get_temperature(self) -> float:
        """Get temperature setting for LLM generation."""
        base_temp = self.advanced_settings.get("temperature", 0.1)
        
        # Adjust based on response style
        style_adjustments = {
            ResponseStyle.FORMAL.value: -0.05,
            ResponseStyle.ACADEMIC.value: -0.05,
            ResponseStyle.TECHNICAL.value: -0.03,
            ResponseStyle.CONVERSATIONAL.value: 0.0,
            ResponseStyle.CASUAL.value: 0.05
        }
        
        adjustment = style_adjustments.get(self.response_style, 0.0)
        return max(0.0, min(1.0, base_temp + adjustment))