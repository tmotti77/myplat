"""Conversation model for chat sessions."""
from enum import Enum
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.base import BaseModel


class ConversationStatus(str, Enum):
    """Conversation status enum."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(BaseModel):
    """Model for storing conversation sessions."""
    
    __tablename__ = "conversations"
    
    # Core fields
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default=ConversationStatus.ACTIVE.value)
    
    # Content and settings
    language = Column(String, default="en")
    mode = Column(String, default="standard")  # RAG mode
    
    # Statistics
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(String, default="0.0")  # Stored as string for precision
    
    # Timestamps
    last_activity_at = Column(DateTime, nullable=True)
    
    # Metadata for customization
    extra_metadata = Column(JSON, default={})
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.last_activity_at:
            self.last_activity_at = func.now()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = func.now()
    
    def add_message_stats(self, tokens: int, cost: float):
        """Update conversation statistics."""
        self.message_count += 1
        self.total_tokens += tokens
        current_cost = float(self.total_cost or "0.0")
        self.total_cost = str(current_cost + cost)
        self.update_activity()