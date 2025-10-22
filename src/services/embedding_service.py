"""Embedding service for generating and managing embeddings."""
import asyncio
from typing import List, Optional, Dict, Any
import random
import math
# Temporarily comment out heavy dependencies
# import numpy as np
# from openai import AsyncOpenAI

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using various models."""
    
    def __init__(self):
        # self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-3-small')
        self.dimensions = getattr(settings, 'EMBEDDING_DIMENSIONS', 1536)
        
    async def generate_embedding(
        self, 
        text: str, 
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding for a single text."""
        model = model or self.default_model
        
        try:
            # Clean and prepare text
            text = text.strip()
            if not text:
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.dimensions
            
            # TODO: Replace with actual OpenAI API call when ML dependencies are available
            # For now, generate a simple hash-based embedding for testing
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to pseudo-embedding
            embedding = []
            for i in range(self.dimensions):
                byte_index = i % len(hash_bytes)
                value = (hash_bytes[byte_index] / 255.0) * 2 - 1  # Scale to [-1, 1]
                embedding.append(float(value))
            
            logger.debug(f"Generated placeholder embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.dimensions
    
    async def generate_batch_embeddings(
        self, 
        texts: List[str], 
        model: Optional[str] = None,
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = []
        
        # Generate embeddings one by one for now
        for text in texts:
            embedding = await self.generate_embedding(text, model)
            embeddings.append(embedding)
            await asyncio.sleep(0.01)  # Small delay
        
        return embeddings
    
    def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Manual cosine similarity calculation without numpy
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            norm1 = math.sqrt(sum(a * a for a in embedding1))
            norm2 = math.sqrt(sum(b * b for b in embedding2))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    async def find_similar_embeddings(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]],
        top_k: int = 10
    ) -> List[tuple]:
        """Find most similar embeddings to query."""
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.calculate_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding is properly formatted."""
        try:
            if not isinstance(embedding, list):
                return False
            
            if len(embedding) != self.dimensions:
                return False
            
            if not all(isinstance(x, (int, float)) for x in embedding):
                return False
            
            # Check for NaN or infinite values
            for x in embedding:
                if math.isnan(x) or math.isinf(x):
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def get_embedding_stats(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """Calculate statistics for a collection of embeddings."""
        try:
            if not embeddings:
                return {"count": 0}
            
            # Basic stats without numpy
            count = len(embeddings)
            dimensions = len(embeddings[0]) if embeddings else 0
            
            # Calculate norms and basic stats
            norms = []
            all_values = []
            
            for embedding in embeddings:
                norm = math.sqrt(sum(x * x for x in embedding))
                norms.append(norm)
                all_values.extend(embedding)
            
            return {
                "count": count,
                "dimensions": dimensions,
                "mean_norm": sum(norms) / len(norms) if norms else 0,
                "min_value": min(all_values) if all_values else 0,
                "max_value": max(all_values) if all_values else 0,
                "mean_value": sum(all_values) / len(all_values) if all_values else 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate embedding stats: {e}")
            return {"count": len(embeddings) if embeddings else 0, "error": str(e)}


# Global instance
embedding_service = EmbeddingService()