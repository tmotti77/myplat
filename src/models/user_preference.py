"""User preference model for personalization."""
from enum import Enum
from sqlalchemy import Column, String, Float, JSON

from src.models.base import BaseModel


class PreferenceType(str, Enum):
    """Types of user preferences."""
    CONTENT_TYPE = "content_type"
    TOPIC = "topic"
    LANGUAGE = "language"
    SOURCE = "source"
    DIFFICULTY = "difficulty"
    LENGTH = "length"
    RECENCY = "recency"
    AUTHOR = "author"


class UserPreference(BaseModel):
    """Model for storing user preferences."""
    
    __tablename__ = "user_preferences"
    
    # Core fields
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Preference details
    preference_type = Column(String, nullable=False)
    category = Column(String, nullable=False)  # e.g., "pdf", "research", "beginner"
    value = Column(String, nullable=False)     # The preferred value
    
    # Preference strength and confidence
    weight = Column(Float, default=1.0)       # How important this preference is
    confidence = Column(Float, default=0.5)   # How confident we are in this preference
    
    # Learning metadata
    interaction_count = Column(String, default="0")  # Number of interactions that built this preference
    last_reinforced = Column(String, nullable=True)   # ISO timestamp of last reinforcement
    
    # Additional context
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def reinforce(self, strength: float = 0.1):
        """Reinforce this preference based on positive interaction."""
        from datetime import datetime
        
        self.weight = min(2.0, self.weight + strength)
        self.confidence = min(1.0, self.confidence + (strength * 0.5))
        self.last_reinforced = datetime.utcnow().isoformat() + "Z"
        
        # Update interaction count
        current_count = int(self.interaction_count or "0")
        self.interaction_count = str(current_count + 1)
    
    def weaken(self, strength: float = 0.1):
        """Weaken this preference based on negative interaction."""
        self.weight = max(0.1, self.weight - strength)
        self.confidence = max(0.1, self.confidence - (strength * 0.3))
    
    def decay(self, decay_rate: float = 0.01):
        """Apply time-based decay to preference strength."""
        self.weight = max(0.1, self.weight * (1 - decay_rate))
        self.confidence = max(0.1, self.confidence * (1 - decay_rate * 0.5))