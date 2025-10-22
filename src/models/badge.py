"""Badge system models for gamification and recognition."""
from enum import Enum
from sqlalchemy import Column, String, Integer, JSON

from src.models.base import BaseModel


class BadgeType(str, Enum):
    """Types of badges available."""
    CONTRIBUTOR = "contributor"
    EXPERT = "expert"
    MASTER = "master"
    PIONEER = "pioneer"
    QUALITY_CHAMPION = "quality_champion"
    PEER_REVIEWER = "peer_reviewer"
    DOMAIN_EXPERT = "domain_expert"
    MENTOR = "mentor"
    INNOVATOR = "innovator"
    TRUSTED = "trusted"
    HELPFUL = "helpful"
    CONSISTENT = "consistent"
    PROLIFIC = "prolific"
    ACCURATE = "accurate"


class BadgeRarity(str, Enum):
    """Badge rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class Badge(BaseModel):
    """Model for badge definitions."""
    
    __tablename__ = "badges"
    
    # Badge details
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    badge_type = Column(String, nullable=False, index=True)
    rarity = Column(String, default=BadgeRarity.COMMON.value)
    
    # Visual elements
    icon_url = Column(String, nullable=True)
    color = Column(String, default="#6B7280")
    
    # Requirements and criteria
    requirements = Column(JSON, default={})
    
    # Gamification
    points_value = Column(Integer, default=10)
    unlock_message = Column(String, nullable=True)
    
    # Statistics
    total_awarded = Column(String, default="0")
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def increment_awarded(self):
        """Increment the total awarded count."""
        current_count = int(self.total_awarded or "0")
        self.total_awarded = str(current_count + 1)
    
    @property
    def awarded_count(self) -> int:
        """Get awarded count as integer."""
        return int(self.total_awarded or "0")


class UserBadge(BaseModel):
    """Model for tracking badges awarded to users."""
    
    __tablename__ = "user_badges"
    
    # Core relationships
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    badge_id = Column(String, nullable=False, index=True)
    
    # Award details
    awarded_at = Column(String, nullable=False)
    awarded_by = Column(String, nullable=True)  # System or admin user ID
    
    # Evidence and context
    evidence = Column(JSON, default={})  # What qualified them for this badge
    achievement_data = Column(JSON, default={})  # Snapshot of stats when earned
    
    # Progress tracking
    progress_when_earned = Column(JSON, default={})
    
    # Display preferences
    is_visible = Column(String, default="true")  # Boolean as string
    is_featured = Column(String, default="false")  # Boolean as string
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.awarded_at:
            from datetime import datetime
            self.awarded_at = datetime.utcnow().isoformat() + "Z"
    
    def make_visible(self):
        """Make badge visible on profile."""
        self.is_visible = "true"
    
    def hide(self):
        """Hide badge from profile."""
        self.is_visible = "false"
    
    def feature(self):
        """Feature this badge prominently."""
        self.is_featured = "true"
    
    def unfeature(self):
        """Remove featured status."""
        self.is_featured = "false"
    
    @property
    def visible(self) -> bool:
        """Check if badge is visible."""
        return self.is_visible == "true"
    
    @property
    def featured(self) -> bool:
        """Check if badge is featured."""
        return self.is_featured == "true"