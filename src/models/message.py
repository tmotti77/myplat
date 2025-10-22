"""Message model for conversation messages."""
from enum import Enum
from sqlalchemy import Column, String, Text, JSON, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class MessageType(str, Enum):
    """Message type enum."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    ERROR = "error"


class MessageRole(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Model for storing conversation messages."""
    
    __tablename__ = "messages"
    
    # Core fields
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String, default=MessageType.TEXT.value)
    
    # Message metrics
    tokens = Column(Integer, nullable=True)
    characters = Column(Integer, nullable=True)
    
    # Processing info
    model_used = Column(String, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    cost_usd = Column(String, nullable=True)  # Stored as string for precision
    
    # Metadata for attachments, citations, etc.
    extra_metadata = Column(JSON, default={})
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.content and not self.characters:
            self.characters = len(self.content)
    
    def set_processing_info(self, model: str, time_ms: int, cost: float, tokens: int = None):
        """Set processing information for the message."""
        self.model_used = model
        self.processing_time_ms = time_ms
        self.cost_usd = str(cost)
        if tokens:
            self.tokens = tokens