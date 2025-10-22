"""RAG event model for analytics and monitoring."""
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON

from src.models.base import BaseModel


class RAGMethod(str, Enum):
    """RAG method enum."""
    VECTOR_ONLY = "vector_only"
    LEXICAL_ONLY = "lexical_only"
    HYBRID_RAG = "hybrid_rag"
    CONVERSATIONAL = "conversational"
    RESEARCH_MODE = "research_mode"


class RAGEvent(BaseModel):
    """Model for tracking RAG operations and performance."""
    
    __tablename__ = "rag_events"
    
    # Core identification
    conversation_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    method = Column(String, nullable=False)
    
    # Input/output content
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    
    # Performance metrics
    sources_retrieved = Column(Integer, default=0)
    response_time_ms = Column(Integer, nullable=False)
    model_used = Column(String, nullable=True)
    total_cost = Column(Float, default=0.0)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    feedback_score = Column(Float, nullable=True)  # User feedback (1-5)
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_feedback(self, score: float, comment: str = None):
        """Set user feedback for this RAG event."""
        self.feedback_score = score
        if comment:
            if not self.extra_metadata:
                self.extra_metadata = {}
            self.extra_metadata["feedback_comment"] = comment
    
    def add_metadata(self, key: str, value):
        """Add metadata to the event."""
        if not self.extra_metadata:
            self.extra_metadata = {}
        self.extra_metadata[key] = value