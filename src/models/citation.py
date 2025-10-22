"""Citation model for linking answers to source chunks."""
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class CitationType(str, Enum):
    """Types of citations."""
    DIRECT_QUOTE = "direct_quote"
    PARAPHRASE = "paraphrase"
    SUMMARY = "summary"
    REFERENCE = "reference"
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"


class Citation(Base):
    """Citation linking answers to source chunks."""
    
    # Answer and chunk relationships
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answer.id"), nullable=False, index=True)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunk.id"), nullable=False, index=True)
    
    # Citation metadata
    citation_type = Column(String(50), nullable=False, default=CitationType.REFERENCE.value)
    order_index = Column(Integer, nullable=False, default=0)  # Order within answer
    
    # Text spans in the answer that reference this chunk
    start_char = Column(Integer, nullable=True)  # Start position in answer text
    end_char = Column(Integer, nullable=True)    # End position in answer text
    span_text = Column(Text)  # The actual text span being cited
    
    # Source information
    source_title = Column(String(1000))  # Document title
    source_url = Column(Text)  # Original URL if available
    source_author = Column(String(500))  # Author if available
    source_date = Column(String(50))  # Publication date (ISO format)
    
    # Chunk context
    chunk_text = Column(Text, nullable=False)  # The cited chunk text
    chunk_section = Column(String(500))  # Section/heading
    chunk_page = Column(Integer)  # Page number if applicable
    
    # Citation quality and relevance
    relevance_score = Column(Float, nullable=False, default=1.0)  # How relevant to the answer
    confidence_score = Column(Float, nullable=False, default=1.0)  # Confidence in citation
    quality_score = Column(Float, nullable=False, default=1.0)  # Overall citation quality
    
    # Position and prominence in answer
    prominence_score = Column(Float, nullable=False, default=0.5)  # How prominent in answer
    is_primary_source = Column(String(10), nullable=False, default="false")  # Boolean as string
    
    # User interaction
    click_count = Column(Integer, nullable=False, default=0)
    helpful_votes = Column(Integer, nullable=False, default=0)
    unhelpful_votes = Column(Integer, nullable=False, default=0)
    
    # Verification and fact-checking
    fact_checked = Column(String(10), nullable=False, default="false")  # Boolean as string
    fact_check_score = Column(Float, nullable=True)  # Fact-checking confidence
    fact_check_notes = Column(Text)  # Notes from fact-checking
    
    # Relationships
    answer = relationship("Answer", back_populates="citations")
    chunk = relationship("Chunk", back_populates="citations")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_citation_answer_order', 'answer_id', 'order_index'),
        Index('idx_citation_chunk_relevance', 'chunk_id', 'relevance_score'),
        Index('idx_citation_type_quality', 'citation_type', 'quality_score'),
        Index('idx_citation_span', 'start_char', 'end_char'),
    )
    
    def __repr__(self) -> str:
        return f"<Citation(answer_id={self.answer_id}, chunk_id={self.chunk_id}, type={self.citation_type})>"
    
    @property
    def is_primary(self) -> bool:
        """Check if this is a primary source citation."""
        return self.is_primary_source == "true"
    
    @property
    def is_fact_checked(self) -> bool:
        """Check if citation has been fact-checked."""
        return self.fact_checked == "true"
    
    @property
    def has_text_span(self) -> bool:
        """Check if citation has a text span in the answer."""
        return self.start_char is not None and self.end_char is not None
    
    @property
    def span_length(self) -> int:
        """Get length of the citation span."""
        if self.has_text_span:
            return self.end_char - self.start_char
        return 0
    
    @property
    def helpfulness_ratio(self) -> float:
        """Calculate helpfulness ratio from votes."""
        total_votes = self.helpful_votes + self.unhelpful_votes
        if total_votes == 0:
            return 0.5  # Neutral when no votes
        return self.helpful_votes / total_votes
    
    def record_click(self):
        """Record that this citation was clicked."""
        self.click_count += 1
    
    def record_helpful_vote(self, helpful: bool):
        """Record a helpfulness vote."""
        if helpful:
            self.helpful_votes += 1
        else:
            self.unhelpful_votes += 1
    
    def set_text_span(self, start: int, end: int, text: str = None):
        """Set the text span for this citation."""
        self.start_char = start
        self.end_char = end
        if text:
            self.span_text = text
    
    def mark_as_primary(self):
        """Mark this citation as a primary source."""
        self.is_primary_source = "true"
        self.prominence_score = min(1.0, self.prominence_score + 0.2)
    
    def mark_fact_checked(self, score: float, notes: str = None):
        """Mark citation as fact-checked with score and optional notes."""
        self.fact_checked = "true"
        self.fact_check_score = max(0.0, min(1.0, score))
        if notes:
            self.fact_check_notes = notes
    
    def calculate_display_priority(self) -> float:
        """Calculate priority for displaying this citation."""
        priority = 0.0
        
        # Relevance is most important
        priority += self.relevance_score * 0.4
        
        # Quality matters
        priority += self.quality_score * 0.2
        
        # Prominence in answer
        priority += self.prominence_score * 0.2
        
        # Primary sources get boost
        if self.is_primary:
            priority += 0.1
        
        # User interaction signals
        if self.click_count > 0:
            click_boost = min(0.1, self.click_count * 0.02)
            priority += click_boost
        
        # Helpfulness votes
        if self.helpful_votes > 0 or self.unhelpful_votes > 0:
            helpfulness_boost = self.helpfulness_ratio * 0.1
            priority += helpfulness_boost
        
        return min(1.0, priority)
    
    def get_source_display_name(self) -> str:
        """Get a display name for the source."""
        if self.source_title:
            # Truncate very long titles
            title = self.source_title[:100] + "..." if len(self.source_title) > 100 else self.source_title
            if self.source_author:
                return f"{title} - {self.source_author}"
            return title
        
        if self.source_url:
            from urllib.parse import urlparse
            domain = urlparse(self.source_url).netloc
            return domain or self.source_url
        
        return "Unknown Source"
    
    def get_preview_text(self, max_length: int = 200) -> str:
        """Get a preview of the cited chunk text."""
        if not self.chunk_text:
            return ""
        
        if len(self.chunk_text) <= max_length:
            return self.chunk_text
        
        # Try to break at sentence boundary
        truncated = self.chunk_text[:max_length]
        last_period = truncated.rfind('.')
        last_space = truncated.rfind(' ')
        
        if last_period > max_length * 0.8:  # If period is reasonably close to end
            return truncated[:last_period + 1]
        elif last_space > max_length * 0.8:  # If space is reasonably close to end
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."