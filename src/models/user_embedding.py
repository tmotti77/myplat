"""User embedding model for personalization."""
from typing import List, Optional

from sqlalchemy import Column, String, Integer, Float, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import ARRAY

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import Text as Vector

from src.models.base import BaseModel


class UserEmbedding(BaseModel):
    """Model for storing user preference embeddings."""
    
    __tablename__ = "user_embeddings"
    
    # Core fields
    user_id = Column(String, nullable=False, index=True, unique=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Model information
    model = Column(String, nullable=False)
    model_version = Column(String, default="1.0")
    dimensions = Column(Integer, nullable=False)
    
    # Vector data
    vector = Column(Vector, nullable=False)
    vector_array = Column(ARRAY(Float), nullable=True)  # Backup storage
    vector_bytes = Column(LargeBinary, nullable=True)   # Binary storage
    
    # Vector properties
    norm = Column(Float, default=1.0)
    is_normalized = Column(String, default="true")
    
    # Learning metadata
    interaction_count = Column(Integer, default=0)
    last_updated = Column(String, nullable=True)
    confidence = Column(Float, default=0.5)
    
    # Quality metrics
    stability_score = Column(Float, default=0.5)  # How stable the embedding is
    coverage_score = Column(Float, default=0.0)   # How well it covers user interests
    
    # Update tracking
    update_count = Column(Integer, default=0)
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def set_vector_from_array(self, vector_array: List[float]):
        """Set vector from Python list."""
        import numpy as np
        
        self.vector = vector_array
        self.vector_array = vector_array
        self.dimensions = len(vector_array)
        
        # Calculate norm
        self.norm = float(np.linalg.norm(vector_array))
        
        # Update metadata
        from datetime import datetime
        self.last_updated = datetime.utcnow().isoformat() + "Z"
        self.update_count += 1
    
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
    
    def calculate_similarity(self, other_vector: List[float]) -> float:
        """Calculate cosine similarity with another vector."""
        import numpy as np
        
        try:
            user_vector = self.get_vector_array()
            if not user_vector:
                return 0.0
            
            v1 = np.array(user_vector)
            v2 = np.array(other_vector)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
            
            if norm_product == 0:
                return 0.0
            
            return float(dot_product / norm_product)
        
        except Exception:
            return 0.0
    
    def update_confidence(self, new_interactions: int):
        """Update confidence based on number of interactions."""
        import numpy as np
        
        total_interactions = self.interaction_count + new_interactions
        self.interaction_count = total_interactions
        
        # Confidence increases with more interactions but plateaus
        self.confidence = min(1.0, 1.0 - np.exp(-total_interactions / 20.0))
    
    def normalize_vector(self):
        """Normalize the vector to unit length."""
        import numpy as np
        
        try:
            vector_array = self.get_vector_array()
            if not vector_array:
                return
            
            v = np.array(vector_array)
            norm = np.linalg.norm(v)
            
            if norm > 0:
                normalized = v / norm
                self.set_vector_from_array(normalized.tolist())
                self.norm = 1.0
                self.is_normalized = "true"
        
        except Exception:
            pass