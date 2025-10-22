"""Answer model for LLM-generated responses."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class AnswerStatus(str, Enum):
    """Answer generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnswerType(str, Enum):
    """Types of generated answers."""
    RAG = "rag"  # Retrieval-augmented generation
    DIRECT = "direct"  # Direct LLM response
    SUMMARY = "summary"  # Document summarization
    EXTRACTION = "extraction"  # Information extraction
    COMPARISON = "comparison"  # Comparative analysis
    TRANSLATION = "translation"  # Language translation


class ConfidenceLevel(str, Enum):
    """Confidence levels for answers."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Answer(Base):
    """Model for LLM-generated answers with full metadata."""
    
    # User and tenant context
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    
    # Query identification
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    parent_answer_id = Column(UUID(as_uuid=True), ForeignKey("answer.id"), nullable=True)
    
    # Question and answer content
    question = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    answer_type = Column(String(50), nullable=False, default=AnswerType.RAG.value)
    
    # Generation metadata
    status = Column(String(50), nullable=False, default=AnswerStatus.COMPLETED.value, index=True)
    model_used = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50))
    
    # Performance metrics
    latency_ms = Column(Float, nullable=False)
    tokens_input = Column(Integer, nullable=False, default=0)
    tokens_output = Column(Integer, nullable=False, default=0)
    tokens_total = Column(Integer, nullable=False, default=0)
    
    # Cost tracking
    cost_usd = Column(Float, nullable=False, default=0.0)
    cost_breakdown = Column(JSON, nullable=False, default={})
    
    # Quality and confidence
    confidence = Column(String(20), nullable=False, default=ConfidenceLevel.MEDIUM.value)
    confidence_score = Column(Float, nullable=False, default=0.5)  # 0-1
    quality_score = Column(Float, nullable=False, default=0.5)  # 0-1
    
    # Content analysis
    sentiment = Column(Float, nullable=True)  # -1 to 1
    readability_score = Column(Float, nullable=True)
    factuality_score = Column(Float, nullable=True)  # Based on grounding
    
    # Language and localization
    language = Column(String(10), nullable=False, default="en", index=True)
    source_language = Column(String(10), nullable=True)  # If translated
    
    # Retrieval context
    retrieval_query_used = Column(Text)  # Query used for retrieval (may differ from user query)
    retrieval_method = Column(String(50))  # hybrid, vector, lexical
    retrieval_count = Column(Integer, nullable=False, default=0)
    retrieval_time_ms = Column(Float, nullable=False, default=0.0)
    
    # Generation configuration
    temperature = Column(Float, nullable=False, default=0.1)
    top_p = Column(Float, nullable=False, default=0.9)
    max_tokens = Column(Integer, nullable=False, default=4000)
    
    # Prompt and context
    system_prompt = Column(Text)
    user_prompt = Column(Text)
    context_chunks_count = Column(Integer, nullable=False, default=0)
    context_length = Column(Integer, nullable=False, default=0)
    
    # Safety and moderation
    flagged_content = Column(Boolean, nullable=False, default=False)
    moderation_results = Column(JSON, nullable=False, default={})
    content_warnings = Column(JSON, nullable=False, default=[])
    
    # User feedback
    user_rating = Column(Float, nullable=True)  # 1-5 stars
    thumbs_up = Column(Boolean, nullable=True)  # True/False/None
    feedback_text = Column(Text)
    feedback_timestamp = Column(String(50))  # ISO timestamp
    
    # Usage tracking
    view_count = Column(Integer, nullable=False, default=1)
    share_count = Column(Integer, nullable=False, default=0)
    bookmark_count = Column(Integer, nullable=False, default=0)
    
    # Follow-up questions suggested
    suggested_questions = Column(JSON, nullable=False, default=[])
    
    # Error tracking
    error_message = Column(Text)
    error_code = Column(String(50))
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Structured output
    structured_data = Column(JSON, nullable=False, default={})
    extracted_entities = Column(JSON, nullable=False, default=[])
    key_points = Column(JSON, nullable=False, default=[])
    
    # Personalization context
    user_preferences_used = Column(JSON, nullable=False, default={})
    personalization_score = Column(Float, nullable=False, default=0.0)
    
    # A/B testing
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiment.id"), nullable=True)
    variant = Column(String(50))
    
    # Audit and compliance
    pii_detected = Column(Boolean, nullable=False, default=False)
    pii_categories = Column(JSON, nullable=False, default=[])
    compliance_flags = Column(JSON, nullable=False, default=[])
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="answers")
    citations = relationship("Citation", back_populates="answer", cascade="all, delete-orphan")
    parent_answer = relationship("Answer", remote_side="Answer.id")
    child_answers = relationship("Answer", back_populates="parent_answer")
    experiment = relationship("Experiment")
    
    def __repr__(self) -> str:
        return f"<Answer(query_id={self.query_id}, model={self.model_used}, confidence={self.confidence})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if answer generation is completed."""
        return self.status == AnswerStatus.COMPLETED.value
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if answer has high confidence."""
        return self.confidence == ConfidenceLevel.HIGH.value
    
    @property
    def cost_cents(self) -> int:
        """Get cost in cents."""
        return int(self.cost_usd * 100)
    
    @property
    def has_citations(self) -> bool:
        """Check if answer has citations."""
        return len(self.citations) > 0
    
    @property
    def citation_count(self) -> int:
        """Get number of citations."""
        return len(self.citations)
    
    @property
    def words_per_second(self) -> float:
        """Calculate generation speed in words per second."""
        if self.latency_ms == 0:
            return 0.0
        
        # Rough estimation: tokens * 0.75 = words
        words = self.tokens_output * 0.75
        seconds = self.latency_ms / 1000
        return words / seconds if seconds > 0 else 0.0
    
    def record_user_feedback(self, rating: float = None, thumbs_up: bool = None, 
                           feedback_text: str = None):
        """Record user feedback for this answer."""
        from datetime import datetime
        
        if rating is not None:
            self.user_rating = max(1.0, min(5.0, rating))
        
        if thumbs_up is not None:
            self.thumbs_up = thumbs_up
        
        if feedback_text:
            self.feedback_text = feedback_text
        
        self.feedback_timestamp = datetime.utcnow().isoformat() + "Z"
    
    def add_suggested_question(self, question: str):
        """Add a suggested follow-up question."""
        if not self.suggested_questions:
            self.suggested_questions = []
        
        if question not in self.suggested_questions:
            self.suggested_questions.append(question)
    
    def get_structured_data(self, key: str, default=None):
        """Get structured data value."""
        return self.structured_data.get(key, default)
    
    def set_structured_data(self, key: str, value):
        """Set structured data value."""
        if not self.structured_data:
            self.structured_data = {}
        self.structured_data[key] = value
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score based on various factors."""
        score = 0.0
        factors = 0
        
        # Confidence factor
        if self.confidence_score:
            score += self.confidence_score
            factors += 1
        
        # Citation factor - answers with citations are generally better
        if self.has_citations:
            citation_score = min(1.0, self.citation_count / 5)  # Normalize to 0-1
            score += citation_score
            factors += 1
        
        # Factuality factor
        if self.factuality_score:
            score += self.factuality_score
            factors += 1
        
        # User feedback factor
        if self.user_rating:
            normalized_rating = (self.user_rating - 1) / 4  # Convert 1-5 to 0-1
            score += normalized_rating
            factors += 1
        elif self.thumbs_up is not None:
            score += 1.0 if self.thumbs_up else 0.0
            factors += 1
        
        # Length appropriateness factor
        if 50 <= self.tokens_output <= 1000:
            score += 1.0
        elif 20 <= self.tokens_output < 50 or 1000 < self.tokens_output <= 2000:
            score += 0.7
        else:
            score += 0.3
        factors += 1
        
        return score / factors if factors > 0 else 0.5
    
    def mark_as_viewed(self):
        """Increment view count."""
        self.view_count += 1
    
    def mark_as_shared(self):
        """Increment share count."""
        self.share_count += 1
    
    def mark_as_bookmarked(self):
        """Increment bookmark count."""
        self.bookmark_count += 1