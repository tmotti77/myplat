"""Chunk model for document text segments."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship

from .base import Base


class ChunkType(str, Enum):
    """Types of content chunks."""
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE = "code"
    QUOTE = "quote"
    FOOTNOTE = "footnote"
    CAPTION = "caption"
    METADATA = "metadata"


class Chunk(Base):
    """Text chunk model for semantic search."""
    
    # Document relationship
    document_id = Column(UUID(as_uuid=True), ForeignKey("document.id"), nullable=False, index=True)
    
    # Position and structure
    idx = Column(Integer, nullable=False)  # Order within document
    section = Column(String(500))  # Section/heading hierarchy
    page_number = Column(Integer)  # Page number if applicable
    
    # Content
    text = Column(Text, nullable=False)
    text_clean = Column(Text)  # Cleaned version without special chars
    chunk_type = Column(String(50), nullable=False, default=ChunkType.TEXT.value)
    
    # Text statistics
    tokens = Column(Integer, nullable=False, default=0)
    characters = Column(Integer, nullable=False, default=0)
    words = Column(Integer, nullable=False, default=0)
    sentences = Column(Integer, nullable=False, default=0)
    
    # Language and encoding
    language = Column(String(10), nullable=False, default="en", index=True)
    language_confidence = Column(Float, nullable=False, default=1.0)
    
    # Content analysis
    readability_score = Column(Float)  # Flesch reading ease score
    sentiment_score = Column(Float)  # -1 to 1
    complexity_score = Column(Float)  # 0 to 1
    
    # Named entities and keywords
    entities = Column(JSON, nullable=False, default=[])  # Named entities found
    keywords = Column(JSON, nullable=False, default=[])  # Extracted keywords
    topics = Column(JSON, nullable=False, default=[])  # Topic classifications
    
    # Context and relationships
    parent_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunk.id"), nullable=True)
    context_before = Column(Text)  # Text from previous chunk for context
    context_after = Column(Text)  # Text from next chunk for context
    
    # Full-text search vector
    search_vector = Column(TSVECTOR)
    
    # Quality and relevance
    quality_score = Column(Float, nullable=False, default=0.8)  # Content quality 0-1
    importance_score = Column(Float, nullable=False, default=0.5)  # Importance within doc 0-1
    
    # Processing metadata
    embedding_model = Column(String(100), nullable=False, default="text-embedding-3-large")
    processed_at = Column(String(50))  # ISO timestamp
    processing_version = Column(String(20), nullable=False, default="1.0")
    
    # Statistics
    retrieval_count = Column(Integer, nullable=False, default=0)
    avg_relevance_score = Column(Float, nullable=False, default=0.0)
    last_retrieved_at = Column(String(50))  # ISO timestamp
    
    # Metadata
    extra_metadata = Column(JSON, nullable=False, default={})
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("Embedding", back_populates="chunk", cascade="all, delete-orphan")
    retrieval_events = relationship("RetrievalEvent", back_populates="chunk")
    citations = relationship("Citation", back_populates="chunk")
    parent_chunk = relationship("Chunk", remote_side="Chunk.id")
    child_chunks = relationship("Chunk", back_populates="parent_chunk")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_chunk_document_position', 'document_id', 'idx'),
        Index('idx_chunk_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_chunk_language_quality', 'language', 'quality_score'),
        Index('idx_chunk_tokens_type', 'tokens', 'chunk_type'),
    )
    
    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, tokens={self.tokens}, type={self.chunk_type})>"
    
    @property
    def text_preview(self) -> str:
        """Get a preview of the chunk text."""
        if len(self.text) <= 100:
            return self.text
        return self.text[:97] + "..."
    
    @property
    def has_embeddings(self) -> bool:
        """Check if chunk has embeddings."""
        return len(self.embeddings) > 0
    
    @property
    def word_density(self) -> float:
        """Calculate word density (words per character)."""
        if self.characters == 0:
            return 0.0
        return self.words / self.characters
    
    def get_embedding(self, model: str = None) -> Optional["Embedding"]:
        """Get embedding for specific model or default."""
        if not self.embeddings:
            return None
        
        if model:
            for embedding in self.embeddings:
                if embedding.model == model:
                    return embedding
        
        # Return first embedding if no model specified
        return self.embeddings[0] if self.embeddings else None
    
    def get_metadata(self, key: str, default=None):
        """Get metadata value by key."""
        return self.extra_metadata.get(key, default)
    
    def set_metadata(self, key: str, value):
        """Set metadata value."""
        if not self.extra_metadata:
            self.extra_metadata = {}
        self.extra_metadata[key] = value
    
    def add_entity(self, entity_type: str, entity_text: str, confidence: float = 1.0):
        """Add a named entity to the chunk."""
        if not self.entities:
            self.entities = []
        
        entity = {
            "type": entity_type,
            "text": entity_text,
            "confidence": confidence
        }
        
        # Avoid duplicates
        for existing in self.entities:
            if existing["type"] == entity_type and existing["text"] == entity_text:
                return
        
        self.entities.append(entity)
    
    def add_keyword(self, keyword: str, score: float = 1.0):
        """Add a keyword to the chunk."""
        if not self.keywords:
            self.keywords = []
        
        keyword_obj = {
            "text": keyword,
            "score": score
        }
        
        # Avoid duplicates
        for existing in self.keywords:
            if existing["text"] == keyword:
                existing["score"] = max(existing["score"], score)
                return
        
        self.keywords.append(keyword_obj)
    
    def update_retrieval_stats(self, relevance_score: float):
        """Update retrieval statistics."""
        from datetime import datetime
        
        self.retrieval_count += 1
        self.last_retrieved_at = datetime.utcnow().isoformat() + "Z"
        
        # Update average relevance score
        if self.avg_relevance_score == 0.0:
            self.avg_relevance_score = relevance_score
        else:
            # Exponential moving average
            alpha = 0.1
            self.avg_relevance_score = (
                alpha * relevance_score + 
                (1 - alpha) * self.avg_relevance_score
            )
    
    def get_context(self, include_before: bool = True, include_after: bool = True) -> str:
        """Get chunk text with context."""
        context_parts = []
        
        if include_before and self.context_before:
            context_parts.append(self.context_before)
        
        context_parts.append(self.text)
        
        if include_after and self.context_after:
            context_parts.append(self.context_after)
        
        return " ".join(context_parts)
    
    def calculate_quality_score(self) -> float:
        """Calculate quality score based on various factors."""
        score = 0.0
        factors = 0
        
        # Length factor - prefer medium-length chunks
        if 100 <= self.tokens <= 800:
            score += 1.0
        elif 50 <= self.tokens < 100 or 800 < self.tokens <= 1200:
            score += 0.7
        else:
            score += 0.3
        factors += 1
        
        # Readability factor
        if self.readability_score:
            # Flesch score: 90-100 very easy, 60-70 standard, 0-30 very difficult
            if 60 <= self.readability_score <= 90:
                score += 1.0
            elif 30 <= self.readability_score < 60 or 90 < self.readability_score <= 100:
                score += 0.7
            else:
                score += 0.3
            factors += 1
        
        # Entity factor - chunks with entities are often more valuable
        if self.entities:
            entity_score = min(1.0, len(self.entities) / 5)  # Normalize to 0-1
            score += entity_score
            factors += 1
        
        # Language confidence factor
        if self.language_confidence:
            score += self.language_confidence
            factors += 1
        
        # Return average if we have factors, otherwise default
        return score / factors if factors > 0 else 0.5