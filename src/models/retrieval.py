"""Models for tracking retrieval events and search results."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class RetrievalMethod(str, Enum):
    """Types of retrieval methods."""
    VECTOR = "vector"
    LEXICAL = "lexical"
    HYBRID = "hybrid"
    RERANK = "rerank"
    MMR = "mmr"


class RetrievalEvent(Base):
    """Track individual retrieval events for analytics and optimization."""
    
    # Query identification
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True)
    
    # Retrieved content
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunk.id"), nullable=False, index=True)
    
    # Retrieval metadata
    method = Column(String(50), nullable=False, index=True)  # vector, lexical, hybrid, etc.
    rank = Column(Integer, nullable=False)  # Position in results (1-indexed)
    score = Column(Float, nullable=False)  # Relevance score
    
    # Original scores from different methods
    vector_score = Column(Float, nullable=True)
    lexical_score = Column(Float, nullable=True)
    rerank_score = Column(Float, nullable=True)
    mmr_score = Column(Float, nullable=True)
    
    # Query context
    query_text = Column(Text, nullable=False)
    query_embedding_model = Column(String(100))
    query_language = Column(String(10), nullable=False, default="en")
    
    # Filters applied
    filters_snapshot = Column(JSON, nullable=False, default={})
    
    # Performance metrics
    retrieval_time_ms = Column(Float, nullable=False)
    total_candidates = Column(Integer, nullable=False, default=0)
    
    # User interaction
    clicked = Column(String(10), nullable=False, default="false")  # Boolean as string
    click_position = Column(Integer, nullable=True)  # Position when clicked
    dwell_time_seconds = Column(Float, nullable=True)  # Time spent on result
    
    # Feedback
    feedback_relevance = Column(Float, nullable=True)  # User feedback on relevance
    feedback_helpful = Column(String(10), nullable=True)  # "true"/"false"/"null"
    feedback_timestamp = Column(String(50))  # ISO timestamp
    
    # Context about the search session
    search_context = Column(JSON, nullable=False, default={})
    
    # Relationships
    chunk = relationship("Chunk", back_populates="retrieval_events")
    user = relationship("User")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_retrieval_query_rank', 'query_id', 'rank'),
        Index('idx_retrieval_method_score', 'method', 'score'),
        Index('idx_retrieval_user_timestamp', 'user_id', 'created_at'),
        Index('idx_retrieval_chunk_score', 'chunk_id', 'score'),
        Index('idx_retrieval_language_method', 'query_language', 'method'),
    )
    
    def __repr__(self) -> str:
        return f"<RetrievalEvent(query_id={self.query_id}, rank={self.rank}, score={self.score:.3f})>"
    
    @property
    def was_clicked(self) -> bool:
        """Check if this result was clicked."""
        return self.clicked == "true"
    
    @property
    def was_helpful(self) -> Optional[bool]:
        """Check if user marked this as helpful."""
        if self.feedback_helpful == "true":
            return True
        elif self.feedback_helpful == "false":
            return False
        return None
    
    def record_click(self, position: int, dwell_time: float = None):
        """Record that this result was clicked."""
        self.clicked = "true"
        self.click_position = position
        if dwell_time is not None:
            self.dwell_time_seconds = dwell_time
    
    def record_feedback(self, relevance: float = None, helpful: bool = None):
        """Record user feedback for this result."""
        from datetime import datetime
        
        if relevance is not None:
            self.feedback_relevance = max(0.0, min(1.0, relevance))
        
        if helpful is not None:
            self.feedback_helpful = "true" if helpful else "false"
        
        self.feedback_timestamp = datetime.utcnow().isoformat() + "Z"
    
    def calculate_dcg_contribution(self, position: int) -> float:
        """Calculate DCG contribution for this result at given position."""
        import math
        
        relevance = self.feedback_relevance or self.score
        return relevance / math.log2(position + 1)
    
    def get_search_context(self, key: str, default=None):
        """Get search context value."""
        return self.search_context.get(key, default)
    
    def set_search_context(self, key: str, value):
        """Set search context value."""
        if not self.search_context:
            self.search_context = {}
        self.search_context[key] = value