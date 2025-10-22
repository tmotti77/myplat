"""Embedding service with OpenAI API and local model support."""
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import openai

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    print("Warning: sentence_transformers not available, local embedding models will be disabled")

try:
    import torch
except ImportError:
    torch = None
    print("Warning: torch not available, local model functionality will be limited")

from src.core.config import settings
from src.core.logging import get_logger, LoggerMixin, log_cost_tracking
from src.models.embedding import EmbeddingModel
from src.services.cache import cache_service

logger = get_logger(__name__)


class EmbeddingService(LoggerMixin):
    """Service for generating embeddings using multiple models."""
    
    def __init__(self):
        self._openai_client = None
        self._local_models = {}
        self._model_cache_ttl = 3600  # 1 hour
        self._device = "cuda" if torch and torch.cuda.is_available() else "cpu"
    
    async def initialize(self):
        """Initialize embedding service."""
        try:
            # Initialize OpenAI client if API key is available
            if settings.OPENAI_API_KEY:
                self._openai_client = openai.AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=60.0,
                    max_retries=3
                )
                self.log_info("OpenAI client initialized for embeddings")
            
            # Pre-load default local model if configured
            if not settings.SKIP_EMBEDDINGS:
                await self._load_local_model(settings.LOCAL_EMBEDDING_MODEL)
            
            self.log_info(
                "Embedding service initialized",
                device=self._device,
                local_models=list(self._local_models.keys())
            )
            
        except Exception as e:
            self.log_error("Failed to initialize embedding service", error=e)
            raise
    
    async def cleanup(self):
        """Clean up embedding service."""
        try:
            # Clear local models from memory
            for model in self._local_models.values():
                if hasattr(model, 'cpu'):
                    model.cpu()
                del model
            
            self._local_models.clear()
            
            # Clear CUDA cache if using GPU
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.log_info("Embedding service cleaned up")
            
        except Exception as e:
            self.log_error("Error during embedding service cleanup", error=e)
    
    async def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        model: str = None,
        tenant_id: str = None,
        use_cache: bool = True,
        batch_size: int = 32
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text(s)."""
        
        # Normalize input
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        if not texts:
            return [] if not is_single else []
        
        # Use default model if not specified
        if not model:
            model = settings.EMBEDDING_MODEL
        
        try:
            # Check cache first
            if use_cache:
                cached_embeddings = await self._get_cached_embeddings(texts, model)
                if cached_embeddings:
                    uncached_texts = []
                    uncached_indices = []
                    for i, (text, embedding) in enumerate(zip(texts, cached_embeddings)):
                        if embedding is None:
                            uncached_texts.append(text)
                            uncached_indices.append(i)
                    
                    # If all are cached, return cached results
                    if not uncached_texts:
                        embeddings = [emb for emb in cached_embeddings if emb is not None]
                        return embeddings[0] if is_single else embeddings
                    
                    # Generate embeddings for uncached texts
                    new_embeddings = await self._generate_embeddings_batch(
                        uncached_texts, model, tenant_id, batch_size
                    )
                    
                    # Merge cached and new embeddings
                    all_embeddings = cached_embeddings.copy()
                    for i, embedding in zip(uncached_indices, new_embeddings):
                        all_embeddings[i] = embedding
                    
                    # Cache new embeddings
                    await self._cache_embeddings(uncached_texts, new_embeddings, model)
                    
                    return all_embeddings[0] if is_single else all_embeddings
            
            # Generate all embeddings
            embeddings = await self._generate_embeddings_batch(
                texts, model, tenant_id, batch_size
            )
            
            # Cache results
            if use_cache:
                await self._cache_embeddings(texts, embeddings, model)
            
            return embeddings[0] if is_single else embeddings
            
        except Exception as e:
            self.log_error(
                "Embedding generation failed",
                model=model,
                text_count=len(texts),
                error=e
            )
            raise
    
    async def _generate_embeddings_batch(
        self,
        texts: List[str],
        model: str,
        tenant_id: str,
        batch_size: int
    ) -> List[List[float]]:
        """Generate embeddings in batches."""
        
        if self._is_openai_model(model):
            return await self._generate_openai_embeddings(texts, model, tenant_id, batch_size)
        else:
            return await self._generate_local_embeddings(texts, model, batch_size)
    
    def _is_openai_model(self, model: str) -> bool:
        """Check if model is an OpenAI model."""
        openai_models = {
            EmbeddingModel.OPENAI_LARGE.value,
            EmbeddingModel.OPENAI_SMALL.value,
            EmbeddingModel.OPENAI_ADA.value,
        }
        return model in openai_models
    
    async def _generate_openai_embeddings(
        self,
        texts: List[str],
        model: str,
        tenant_id: str,
        batch_size: int
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        
        if not self._openai_client:
            raise ValueError("OpenAI client not initialized")
        
        all_embeddings = []
        total_tokens = 0
        total_cost = 0.0
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                start_time = time.time()
                
                # Call OpenAI API
                response = await self._openai_client.embeddings.create(
                    model=model,
                    input=batch,
                    encoding_format="float"
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract embeddings
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Track usage and costs
                batch_tokens = response.usage.total_tokens
                total_tokens += batch_tokens
                
                batch_cost = self._calculate_openai_cost(model, batch_tokens)
                total_cost += batch_cost
                
                self.log_info(
                    "OpenAI embeddings generated",
                    model=model,
                    batch_size=len(batch),
                    tokens=batch_tokens,
                    cost_usd=batch_cost,
                    duration_ms=duration_ms
                )
                
                # Rate limiting - avoid hitting API limits
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)  # Small delay between batches
                
            except Exception as e:
                self.log_error(
                    "OpenAI embedding batch failed",
                    model=model,
                    batch_start=i,
                    batch_size=len(batch),
                    error=e
                )
                raise
        
        # Log total cost
        if total_cost > 0:
            log_cost_tracking(
                "embedding_generation",
                total_cost,
                model=model,
                tenant_id=tenant_id,
                tokens=total_tokens,
                text_count=len(texts)
            )
        
        return all_embeddings
    
    async def _generate_local_embeddings(
        self,
        texts: List[str],
        model: str,
        batch_size: int
    ) -> List[List[float]]:
        """Generate embeddings using local model."""
        
        # Load model if not already loaded
        sentence_model = await self._load_local_model(model)
        
        try:
            start_time = time.time()
            
            # Generate embeddings in thread pool to avoid blocking
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None,
                self._encode_texts_sync,
                sentence_model,
                texts,
                batch_size
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.log_info(
                "Local embeddings generated",
                model=model,
                text_count=len(texts),
                duration_ms=duration_ms,
                device=self._device
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            self.log_error(
                "Local embedding generation failed",
                model=model,
                text_count=len(texts),
                error=e
            )
            raise
    
    def _encode_texts_sync(
        self,
        model: SentenceTransformer,
        texts: List[str],
        batch_size: int
    ) -> np.ndarray:
        """Synchronous text encoding for thread pool."""
        
        return model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
    
    async def _load_local_model(self, model_name: str) -> Optional[object]:
        """Load local embedding model."""
        
        if SentenceTransformer is None:
            self.log_warning("SentenceTransformer not available, cannot load local model")
            return None
            
        if model_name in self._local_models:
            return self._local_models[model_name]
        
        try:
            self.log_info("Loading local embedding model", model=model_name)
            
            # Load model in thread pool
            sentence_model = await asyncio.get_event_loop().run_in_executor(
                None,
                self._load_sentence_transformer,
                model_name
            )
            
            # Move to appropriate device
            if torch:
                sentence_model = sentence_model.to(self._device)
            
            # Cache model
            self._local_models[model_name] = sentence_model
            
            self.log_info(
                "Local embedding model loaded",
                model=model_name,
                device=self._device
            )
            
            return sentence_model
            
        except Exception as e:
            self.log_error("Failed to load local model", model=model_name, error=e)
            raise
    
    def _load_sentence_transformer(self, model_name: str) -> Optional[object]:
        """Load SentenceTransformer model synchronously."""
        
        if SentenceTransformer is None:
            return None
            
        return SentenceTransformer(
            model_name,
            device=self._device,
            trust_remote_code=False
        )
    
    def _calculate_openai_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for OpenAI embedding generation."""
        
        # Cost per 1k tokens (as of 2024)
        cost_per_1k = {
            EmbeddingModel.OPENAI_LARGE.value: 0.00013,
            EmbeddingModel.OPENAI_SMALL.value: 0.00002,
            EmbeddingModel.OPENAI_ADA.value: 0.0001,
        }
        
        rate = cost_per_1k.get(model, 0.0001)
        return (tokens / 1000) * rate
    
    async def _get_cached_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> Optional[List[Optional[List[float]]]]:
        """Get cached embeddings for texts."""
        
        try:
            # Generate cache keys
            cache_keys = [
                self._get_embedding_cache_key(text, model)
                for text in texts
            ]
            
            # Get from cache
            cached_data = await cache_service.get_many(cache_keys)
            
            return [cached_data.get(key) for key in cache_keys]
            
        except Exception as e:
            self.log_warning("Cache retrieval failed for embeddings", error=e)
            return None
    
    async def _cache_embeddings(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        model: str
    ):
        """Cache embeddings for texts."""
        
        try:
            # Prepare cache data
            cache_data = {}
            for text, embedding in zip(texts, embeddings):
                cache_key = self._get_embedding_cache_key(text, model)
                cache_data[cache_key] = embedding
            
            # Cache with TTL
            await cache_service.set_many(cache_data, ttl=self._model_cache_ttl)
            
        except Exception as e:
            self.log_warning("Cache storage failed for embeddings", error=e)
    
    def _get_embedding_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for embedding."""
        
        import hashlib
        
        # Create hash of text for consistent key
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        
        return f"embedding:{model}:{text_hash}"
    
    async def get_embedding_dimensions(self, model: str) -> int:
        """Get embedding dimensions for a model."""
        
        dimensions = {
            EmbeddingModel.OPENAI_LARGE.value: 3072,
            EmbeddingModel.OPENAI_SMALL.value: 1536,
            EmbeddingModel.OPENAI_ADA.value: 1536,
            EmbeddingModel.BGE_M3.value: 1024,
            EmbeddingModel.BGE_LARGE.value: 1024,
            EmbeddingModel.BGE_BASE.value: 768,
            EmbeddingModel.SENTENCE_TRANSFORMER.value: 384,
            EmbeddingModel.MULTILINGUAL.value: 384,
        }
        
        if model in dimensions:
            return dimensions[model]
        
        # For unknown models, generate a test embedding
        try:
            test_embedding = await self.generate_embeddings("test", model)
            return len(test_embedding)
        except Exception as e:
            self.log_error("Failed to determine embedding dimensions", model=model, error=e)
            return 1536  # Default fallback
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """Perform similarity search using cosine similarity."""
        
        try:
            # Convert to numpy arrays
            query_vec = np.array(query_embedding)
            candidate_vecs = np.array(candidate_embeddings)
            
            # Normalize vectors
            query_norm = query_vec / np.linalg.norm(query_vec)
            candidate_norms = candidate_vecs / np.linalg.norm(candidate_vecs, axis=1, keepdims=True)
            
            # Calculate cosine similarities
            similarities = np.dot(candidate_norms, query_norm)
            
            # Get top-k indices and scores
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = [
                (int(idx), float(similarities[idx]))
                for idx in top_indices
            ]
            
            return results
            
        except Exception as e:
            self.log_error("Similarity search failed", error=e)
            raise
    
    async def batch_similarity_search(
        self,
        query_embeddings: List[List[float]],
        candidate_embeddings: List[List[float]],
        top_k: int = 10
    ) -> List[List[Tuple[int, float]]]:
        """Perform batch similarity search."""
        
        try:
            results = []
            
            for query_embedding in query_embeddings:
                query_results = await self.similarity_search(
                    query_embedding,
                    candidate_embeddings,
                    top_k
                )
                results.append(query_results)
            
            return results
            
        except Exception as e:
            self.log_error("Batch similarity search failed", error=e)
            raise
    
    async def health_check(self) -> Dict[str, any]:
        """Check embedding service health."""
        
        health = {
            "status": "healthy",
            "models_loaded": list(self._local_models.keys()),
            "device": self._device,
            "openai_available": self._openai_client is not None,
            "gpu_available": torch.cuda.is_available(),
        }
        
        if torch.cuda.is_available():
            health["gpu_memory_allocated"] = torch.cuda.memory_allocated()
            health["gpu_memory_cached"] = torch.cuda.memory_reserved()
        
        try:
            # Test embedding generation
            test_embedding = await self.generate_embeddings(
                "health check test",
                model=settings.LOCAL_EMBEDDING_MODEL
            )
            health["test_embedding_length"] = len(test_embedding)
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


# Global embedding service instance
embedding_service = EmbeddingService()