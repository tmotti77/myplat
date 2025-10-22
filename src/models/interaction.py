"""User interaction model for tracking behavior."""
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, JSON

from src.models.base import BaseModel


class InteractionType(str, Enum):
    """Types of user interactions."""
    VIEW = "view"
    CLICK = "click"
    LIKE = "like"
    DISLIKE = "dislike"
    SHARE = "share"
    BOOKMARK = "bookmark"
    DOWNLOAD = "download"
    SEARCH = "search"
    DWELL = "dwell"
    SKIP = "skip"
    RATE = "rate"
    COMMENT = "comment"


class Interaction(BaseModel):
    """Model for tracking user interactions with content."""
    
    __tablename__ = "interactions"
    
    # Core fields
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Content identification
    content_id = Column(String, nullable=False, index=True)  # document_id, chunk_id, etc.
    content_type = Column(String, nullable=False)  # document, chunk, query, etc.
    
    # Interaction details
    interaction_type = Column(String, nullable=False, index=True)
    
    # Explicit feedback
    explicit_rating = Column(Float, nullable=True)  # 1-5 star rating
    explicit_feedback = Column(String, nullable=True)  # text feedback
    
    # Implicit signals
    dwell_time_seconds = Column(Float, nullable=True)
    scroll_percentage = Column(Float, nullable=True)
    clicks_count = Column(Integer, default=0)
    
    # Context
    session_id = Column(String, nullable=True, index=True)
    query_context = Column(String, nullable=True)  # search query that led to this
    source_context = Column(String, nullable=True)  # where user came from
    
    # Timing
    interaction_timestamp = Column(String, nullable=False)  # ISO timestamp
    
    # Additional signals
    implicit_signals = Column(JSON, default={})  # Additional implicit feedback
    extra_metadata = Column(JSON, default={})  # Extra context
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.interaction_timestamp:
            from datetime import datetime
            self.interaction_timestamp = datetime.utcnow().isoformat() + "Z"
    
    def get_implicit_score(self) -> float:
        """Calculate implicit preference score from signals."""
        score = 0.0
        
        # Dwell time scoring
        if self.dwell_time_seconds:
            if self.dwell_time_seconds > 300:  # 5+ minutes
                score += 1.0
            elif self.dwell_time_seconds > 120:  # 2+ minutes
                score += 0.7
            elif self.dwell_time_seconds > 30:  # 30+ seconds
                score += 0.5
            elif self.dwell_time_seconds > 10:  # 10+ seconds
                score += 0.3
            else:
                score += 0.1
        
        # Scroll percentage scoring
        if self.scroll_percentage:
            if self.scroll_percentage > 0.8:  # Read most of content
                score += 0.5
            elif self.scroll_percentage > 0.5:  # Read half
                score += 0.3
            elif self.scroll_percentage > 0.2:  # Skimmed
                score += 0.1
        
        # Click engagement
        if self.clicks_count:
            score += min(0.3, self.clicks_count * 0.1)
        
        # Interaction type modifiers
        type_scores = {
            InteractionType.LIKE: 1.0,
            InteractionType.BOOKMARK: 0.9,
            InteractionType.SHARE: 0.8,
            InteractionType.DOWNLOAD: 0.7,
            InteractionType.COMMENT: 0.6,
            InteractionType.CLICK: 0.4,
            InteractionType.VIEW: 0.3,
            InteractionType.DWELL: 0.2,
            InteractionType.DISLIKE: -0.5,
            InteractionType.SKIP: -0.2,
        }
        
        interaction_modifier = type_scores.get(
            InteractionType(self.interaction_type), 0.0
        )
        score *= (1.0 + interaction_modifier)
        
        return max(-1.0, min(1.0, score))  # Clamp to [-1, 1]
    
    def get_total_preference_score(self) -> float:
        """Get combined explicit and implicit preference score."""
        explicit_score = 0.0
        if self.explicit_rating:
            # Convert 1-5 rating to -1 to 1 scale
            explicit_score = (self.explicit_rating - 3.0) / 2.0
        
        implicit_score = self.get_implicit_score()
        
        # Weight explicit feedback more heavily
        if self.explicit_rating:
            return 0.7 * explicit_score + 0.3 * implicit_score
        else:
            return implicit_score
    
    def is_positive_interaction(self) -> bool:
        """Check if this represents positive user feedback."""
        positive_types = {
            InteractionType.LIKE,
            InteractionType.BOOKMARK,
            InteractionType.SHARE,
            InteractionType.DOWNLOAD,
            InteractionType.COMMENT
        }
        
        if InteractionType(self.interaction_type) in positive_types:
            return True
        
        if self.explicit_rating and self.explicit_rating >= 4.0:
            return True
        
        if self.get_implicit_score() > 0.5:
            return True
        
        return False
    
    def is_negative_interaction(self) -> bool:
        """Check if this represents negative user feedback."""
        negative_types = {
            InteractionType.DISLIKE,
            InteractionType.SKIP
        }
        
        if InteractionType(self.interaction_type) in negative_types:
            return True
        
        if self.explicit_rating and self.explicit_rating <= 2.0:
            return True
        
        if self.get_implicit_score() < -0.3:
            return True
        
        return False