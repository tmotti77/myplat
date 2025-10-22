"""Embedding model for vector representations."""
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, String, Integer, ForeignKey, Float, Index, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for when pgvector is not available
    from sqlalchemy import Text as Vector

from .base import Base


class EmbeddingModel(str, Enum):
    """Supported embedding models."""
    OPENAI_LARGE = "text-embedding-3-large"
    OPENAI_SMALL = "text-embedding-3-small"
    OPENAI_ADA = "text-embedding-ada-002"
    BGE_M3 = "BAAI/bge-m3"
    BGE_LARGE = "BAAI/bge-large-en-v1.5"
    BGE_BASE = "BAAI/bge-base-en-v1.5"
    SENTENCE_TRANSFORMER = "all-MiniLM-L6-v2"
    MULTILINGUAL = "paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingStatus(str, Enum):
    """Embedding generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Embedding(Base):
    """Vector embedding model for semantic search."""
    
    # Chunk relationship
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunk.id"), nullable=False, index=True)
    
    # Model information
    model = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, default="1.0")
    dimensions = Column(Integer, nullable=False)
    
    # Vector data
    vector = Column(Vector, nullable=False)  # Will be Vector(dimensions) in real usage
    
    # Alternative storage for compatibility
    vector_bytes = Column(LargeBinary, nullable=True)  # Binary representation
    vector_array = Column(ARRAY(Float), nullable=True)  # Array representation
    
    # Vector properties
    norm = Column(Float, nullable=False, default=1.0)  # L2 norm
    is_normalized = Column(String(10), nullable=False, default="true")  # Boolean as string
    
    # Generation metadata
    status = Column(String(50), nullable=False, default=EmbeddingStatus.COMPLETED.value)
    generated_at = Column(String(50), nullable=False)  # ISO timestamp
    generation_time_ms = Column(Float)  # Generation time in milliseconds
    
    # Quality metrics
    quality_score = Column(Float, nullable=False, default=1.0)  # 0-1 based on generation confidence
    confidence = Column(Float, nullable=False, default=1.0)  # Model confidence
    
    # Usage statistics
    search_count = Column(Integer, nullable=False, default=0)  # Times used in search
    similarity_sum = Column(Float, nullable=False, default=0.0)  # Sum of similarity scores
    avg_similarity = Column(Float, nullable=False, default=0.0)  # Average similarity when retrieved
    
    # Cost tracking
    cost_usd = Column(Float, nullable=False, default=0.0)  # Cost to generate in USD
    tokens_used = Column(Integer, nullable=False, default=0)  # Tokens used for generation
    
    # Configuration used for generation
    config = Column(String(1000), nullable=False, default="{}")  # JSON string of config used
    
    # Error tracking
    last_error = Column(String(2000))
    error_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    chunk = relationship("Chunk", back_populates="embeddings")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_embedding_chunk_model', 'chunk_id', 'model'),
        Index('idx_embedding_model_status', 'model', 'status'),
        Index('idx_embedding_vector', 'vector', postgresql_using='ivfflat', 
              postgresql_ops={'vector': 'vector_cosine_ops'}),
        Index('idx_embedding_generated_at', 'generated_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Embedding(chunk_id={self.chunk_id}, model={self.model}, dim={self.dimensions})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if embedding generation is completed."""
        return self.status == EmbeddingStatus.COMPLETED.value
    
    @property
    def generation_cost_cents(self) -> int:
        """Get generation cost in cents."""
        return int(self.cost_usd * 100)
    
    def calculate_similarity(self, other_vector: List[float]) -> float:
        """Calculate cosine similarity with another vector."""
        import numpy as np
        
        try:
            # Convert vector to numpy array if needed
            if hasattr(self.vector, '__iter__'):
                v1 = np.array(self.vector)
            else:
                # Handle pgvector type
                v1 = np.array(list(self.vector))
            
            v2 = np.array(other_vector)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
            
            if norm_product == 0:
                return 0.0
            
            return float(dot_product / norm_product)
        
        except Exception:
            return 0.0
    
    def update_search_stats(self, similarity_score: float):
        """Update search usage statistics."""
        self.search_count += 1
        self.similarity_sum += similarity_score
        self.avg_similarity = self.similarity_sum / self.search_count
    
    def normalize_vector(self):
        """Normalize the vector to unit length."""
        import numpy as np
        
        try:
            if hasattr(self.vector, '__iter__'):
                v = np.array(self.vector)
            else:
                v = np.array(list(self.vector))
            
            norm = np.linalg.norm(v)
            if norm > 0:
                normalized = v / norm
                self.vector = normalized.tolist()
                self.norm = 1.0
                self.is_normalized = "true"
            
        except Exception as e:
            self.last_error = f"Normalization failed: {str(e)}"
            self.error_count += 1
    
    def get_vector_array(self) -> Optional[List[float]]:
        """Get vector as Python list."""
        try:
            if self.vector_array:
                return list(self.vector_array)
            elif hasattr(self.vector, '__iter__'):
                return list(self.vector)
            else:
                return list(self.vector)
        except:
            return None
    
    def set_vector_from_array(self, vector_array: List[float]):
        """Set vector from Python list."""
        self.vector = vector_array
        self.vector_array = vector_array
        self.dimensions = len(vector_array)
        
        # Calculate norm
        import numpy as np
        self.norm = float(np.linalg.norm(vector_array))
    
    @classmethod
    def get_model_dimensions(cls, model: str) -> int:
        """Get expected dimensions for a model."""
        model_dims = {
            EmbeddingModel.OPENAI_LARGE.value: 3072,
            EmbeddingModel.OPENAI_SMALL.value: 1536,
            EmbeddingModel.OPENAI_ADA.value: 1536,
            EmbeddingModel.BGE_M3.value: 1024,
            EmbeddingModel.BGE_LARGE.value: 1024,
            EmbeddingModel.BGE_BASE.value: 768,
            EmbeddingModel.SENTENCE_TRANSFORMER.value: 384,
            EmbeddingModel.MULTILINGUAL.value: 384,
        }
        return model_dims.get(model, 1536)  # Default to 1536
    
    @classmethod
    def estimate_cost(cls, model: str, tokens: int) -> float:
        """Estimate cost for generating embedding."""
        # Cost per 1k tokens in USD (approximate)
        cost_per_1k = {
            EmbeddingModel.OPENAI_LARGE.value: 0.00013,
            EmbeddingModel.OPENAI_SMALL.value: 0.00002,
            EmbeddingModel.OPENAI_ADA.value: 0.0001,
            EmbeddingModel.BGE_M3.value: 0.0,  # Local model
            EmbeddingModel.BGE_LARGE.value: 0.0,  # Local model
            EmbeddingModel.BGE_BASE.value: 0.0,  # Local model
            EmbeddingModel.SENTENCE_TRANSFORMER.value: 0.0,  # Local model
            EmbeddingModel.MULTILINGUAL.value: 0.0,  # Local model
        }
        
        rate = cost_per_1k.get(model, 0.0001)
        return (tokens / 1000) * rate