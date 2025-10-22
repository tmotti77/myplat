"""Hybrid search service combining vector search, FTS, and re-ranking."""
import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
try:
    from elasticsearch import AsyncElasticsearch
except ImportError:
    AsyncElasticsearch = None
    print("Warning: elasticsearch not available, search functionality will be limited")

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None
    print("Warning: sentence_transformers not available, re-ranking functionality will be disabled")

from src.core.config import settings
from src.core.database import get_db_session
from src.core.logging import get_logger, LoggerMixin, log_performance
from src.models.chunk import Chunk
from src.models.document import Document
from src.models.retrieval import RetrievalEvent, RetrievalMethod
from src.services.cache import cache_service
from src.services.embedding import embedding_service
from src.services.vector_store import vector_store_service
from sqlalchemy import select, text, func
from sqlalchemy.orm import joinedload

logger = get_logger(__name__)


class SearchService(LoggerMixin):
    """Hybrid search service with vector search, FTS, and re-ranking."""
    
    def __init__(self):
        self._es_client: Optional[AsyncElasticsearch] = None
        self._reranker_model = None
        self._reranker_cache_ttl = 3600  # 1 hour
    
    async def initialize(self):
        """Initialize search service components."""
        try:
            # Initialize Elasticsearch client
            if AsyncElasticsearch is not None and settings.ELASTICSEARCH_URL:
                auth = None
                if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
                    auth = (settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
                
                self._es_client = AsyncElasticsearch(
                    [settings.ELASTICSEARCH_URL],
                    basic_auth=auth,
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
                
                # Test connection
                await self._es_client.ping()
                self.log_info("Elasticsearch client initialized")
            
            # Load re-ranking model
            await self._load_reranker_model()
            
            self.log_info("Search service initialized")
            
        except Exception as e:
            self.log_error("Failed to initialize search service", error=e)
            raise
    
    async def cleanup(self):
        """Clean up search service."""
        try:
            if self._es_client:
                await self._es_client.close()
            
            # Clean up re-ranker model
            if self._reranker_model:
                del self._reranker_model
                self._reranker_model = None
            
            self.log_info("Search service cleaned up")
            
        except Exception as e:
            self.log_error("Error during search cleanup", error=e)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check search service health."""
        health = {
            "status": "healthy",
            "elasticsearch_available": False,
            "vector_store_available": False,
            "reranker_loaded": self._reranker_model is not None,
        }
        
        try:
            # Check Elasticsearch
            if self._es_client:
                es_health = await self._es_client.ping()
                health["elasticsearch_available"] = es_health
            
            # Check vector store
            vs_health = await vector_store_service.health_check()
            health["vector_store_available"] = vs_health
            
            if not (health["elasticsearch_available"] or health["vector_store_available"]):
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health
    
    async def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        k: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        use_mmr: bool = True,
        embedding_model: str = None,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and lexical search."""
        
        start_time = time.time()
        
        try:
            # Use default embedding model if not specified
            if not embedding_model:
                embedding_model = settings.EMBEDDING_MODEL
            
            # Execute vector and lexical searches in parallel
            vector_task = self._vector_search(
                query, tenant_id, embedding_model, k, filters, language
            )
            lexical_task = self._lexical_search(
                query, tenant_id, k, filters, language
            )
            
            vector_results, lexical_results = await asyncio.gather(
                vector_task, lexical_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vector_results, Exception):
                self.log_error("Vector search failed", error=vector_results)
                vector_results = []
            
            if isinstance(lexical_results, Exception):
                self.log_error("Lexical search failed", error=lexical_results)
                lexical_results = []
            
            # Combine and deduplicate results
            combined_results = await self._combine_search_results(
                vector_results, lexical_results, k
            )
            
            # Apply MMR for diversity if requested
            if use_mmr and len(combined_results) > k:
                combined_results = await self._apply_mmr(
                    query, combined_results, k, embedding_model
                )
            
            # Re-rank results if requested
            if rerank and len(combined_results) > 1:
                combined_results = await self._rerank_results(
                    query, combined_results
                )
            
            # Log retrieval events for analytics
            await self._log_retrieval_events(
                query, combined_results, user_id, tenant_id, language
            )
            
            # Performance logging
            duration_ms = (time.time() - start_time) * 1000
            log_performance(
                "hybrid_search",
                duration_ms,
                query_length=len(query),
                results_count=len(combined_results),
                k=k,
                rerank=rerank,
                use_mmr=use_mmr
            )
            
            return combined_results
            
        except Exception as e:
            self.log_error(
                "Hybrid search failed",
                query=query[:100],  # Truncate for logging
                tenant_id=tenant_id,
                error=e
            )
            raise
    
    async def _vector_search(
        self,
        query: str,
        tenant_id: str,
        embedding_model: str,
        k: int,
        filters: Optional[Dict[str, Any]],
        language: str
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        
        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_embeddings(
                query, embedding_model, tenant_id
            )
            
            # Prepare filters for vector store
            vector_filters = {}
            if filters:
                vector_filters.update(filters)
            
            # Add language filter
            vector_filters["language"] = language
            vector_filters["tenant_id"] = tenant_id
            
            # Search in vector store
            vector_results = await vector_store_service.search_vectors(
                tenant_id=tenant_id,
                embedding_model=embedding_model,
                query_vector=query_embedding,
                limit=k * 2,  # Get more for better hybrid combination
                filters=vector_filters
            )
            
            # Enrich with chunk data
            enriched_results = []
            for result in vector_results:
                chunk_data = await self._get_chunk_data(result["id"])
                if chunk_data:
                    enriched_results.append({
                        "chunk_id": result["id"],
                        "vector_score": result["score"],
                        "method": RetrievalMethod.VECTOR.value,
                        **chunk_data
                    })
            
            return enriched_results
            
        except Exception as e:
            self.log_error("Vector search failed", error=e)
            return []
    
    async def _lexical_search(
        self,
        query: str,
        tenant_id: str,
        k: int,
        filters: Optional[Dict[str, Any]],
        language: str
    ) -> List[Dict[str, Any]]:
        """Perform lexical/keyword search using PostgreSQL FTS."""
        
        try:
            async with get_db_session() as session:
                # Build base query
                query_stmt = (
                    select(Chunk)
                    .join(Document)
                    .options(joinedload(Chunk.document))
                    .where(Document.tenant_id == tenant_id)
                    .where(Chunk.language == language)
                )
                
                # Add full-text search
                # Use PostgreSQL's built-in FTS with ranking
                ts_query = text("plainto_tsquery(:query)")
                rank_expr = func.ts_rank_cd(Chunk.search_vector, ts_query)
                
                query_stmt = query_stmt.where(
                    Chunk.search_vector.op("@@")(ts_query)
                ).order_by(rank_expr.desc())
                
                # Apply additional filters
                if filters:
                    if "source_ids" in filters:
                        query_stmt = query_stmt.where(
                            Document.source_id.in_(filters["source_ids"])
                        )
                    
                    if "content_types" in filters:
                        query_stmt = query_stmt.where(
                            Document.content_type.in_(filters["content_types"])
                        )
                    
                    if "min_quality" in filters:
                        query_stmt = query_stmt.where(
                            Chunk.quality_score >= filters["min_quality"]
                        )
                
                # Limit results
                query_stmt = query_stmt.limit(k * 2)
                
                # Execute query
                result = await session.execute(
                    query_stmt.params(query=query)
                )
                chunks = result.unique().scalars().all()
                
                # Format results
                lexical_results = []
                for chunk in chunks:
                    # Calculate lexical score (simplified)
                    lexical_score = await self._calculate_lexical_score(
                        query, chunk.text
                    )
                    
                    lexical_results.append({
                        "chunk_id": str(chunk.id),
                        "lexical_score": lexical_score,
                        "method": RetrievalMethod.LEXICAL.value,
                        "text": chunk.text,
                        "tokens": chunk.tokens,
                        "chunk_type": chunk.chunk_type,
                        "section": chunk.section,
                        "page_number": chunk.page_number,
                        "quality_score": chunk.quality_score,
                        "document_id": str(chunk.document_id),
                        "document_title": chunk.document.title,
                        "document_url": chunk.document.url,
                        "source_id": str(chunk.document.source_id),
                    })
                
                return lexical_results
                
        except Exception as e:
            self.log_error("Lexical search failed", error=e)
            return []
    
    async def _elasticsearch_search(
        self,
        query: str,
        tenant_id: str,
        k: int,
        filters: Optional[Dict[str, Any]],
        language: str
    ) -> List[Dict[str, Any]]:
        """Perform Elasticsearch search (if available)."""
        
        if not self._es_client:
            return []
        
        try:
            # Build Elasticsearch query
            es_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["text^2", "section", "document_title"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"tenant_id": tenant_id}},
                        {"term": {"language": language}}
                    ]
                }
            }
            
            # Add additional filters
            if filters:
                if "source_ids" in filters:
                    es_query["bool"]["filter"].append({
                        "terms": {"source_id": filters["source_ids"]}
                    })
                
                if "content_types" in filters:
                    es_query["bool"]["filter"].append({
                        "terms": {"document_content_type": filters["content_types"]}
                    })
            
            # Execute search
            index_name = f"chunks_{tenant_id}"
            response = await self._es_client.search(
                index=index_name,
                query=es_query,
                size=k * 2,
                sort=[{"_score": {"order": "desc"}}]
            )
            
            # Format results
            es_results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                es_results.append({
                    "chunk_id": source["chunk_id"],
                    "lexical_score": hit["_score"],
                    "method": RetrievalMethod.LEXICAL.value,
                    **source
                })
            
            return es_results
            
        except Exception as e:
            self.log_error("Elasticsearch search failed", error=e)
            return []
    
    async def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        lexical_results: List[Dict[str, Any]],
        k: int
    ) -> List[Dict[str, Any]]:
        """Combine vector and lexical search results with hybrid scoring."""
        
        # Create lookup for chunk IDs
        vector_lookup = {r["chunk_id"]: r for r in vector_results}
        lexical_lookup = {r["chunk_id"]: r for r in lexical_results}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(vector_lookup.keys()) | set(lexical_lookup.keys())
        
        # Combine results with hybrid scoring
        combined_results = []
        
        for chunk_id in all_chunk_ids:
            vector_result = vector_lookup.get(chunk_id)
            lexical_result = lexical_lookup.get(chunk_id)
            
            # Normalize scores (0-1 range)
            vector_score = vector_result["vector_score"] if vector_result else 0.0
            lexical_score = self._normalize_lexical_score(
                lexical_result["lexical_score"] if lexical_result else 0.0
            )
            
            # Calculate hybrid score (weighted combination)
            hybrid_score = (
                0.7 * vector_score +  # Vector search weight
                0.3 * lexical_score   # Lexical search weight
            )
            
            # Use vector result as base, fall back to lexical
            base_result = vector_result or lexical_result
            
            combined_result = {
                **base_result,
                "vector_score": vector_score,
                "lexical_score": lexical_score,
                "hybrid_score": hybrid_score,
                "method": RetrievalMethod.HYBRID.value
            }
            
            combined_results.append(combined_result)
        
        # Sort by hybrid score and limit
        combined_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return combined_results[:k]
    
    def _normalize_lexical_score(self, score: float) -> float:
        """Normalize lexical search score to 0-1 range."""
        
        # This is a simplified normalization
        # In practice, you'd use more sophisticated methods
        return min(1.0, score / 10.0)  # Adjust divisor based on your scoring
    
    async def _apply_mmr(
        self,
        query: str,
        results: List[Dict[str, Any]],
        k: int,
        embedding_model: str,
        lambda_param: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Apply Maximal Marginal Relevance for result diversification."""
        
        try:
            if len(results) <= k:
                return results
            
            # Get query embedding
            query_embedding = await embedding_service.generate_embeddings(
                query, embedding_model
            )
            
            # Get embeddings for all results (from cache or generate)
            result_embeddings = []
            for result in results:
                # Try to get from vector search result first
                if "vector" in result:
                    result_embeddings.append(result["vector"])
                else:
                    # Generate embedding for text
                    embedding = await embedding_service.generate_embeddings(
                        result["text"][:500],  # Truncate for efficiency
                        embedding_model
                    )
                    result_embeddings.append(embedding)
            
            # Apply MMR algorithm
            selected_indices = []
            remaining_indices = list(range(len(results)))
            
            # Select first result (highest relevance)
            best_idx = 0
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
            
            # Select remaining results using MMR
            while len(selected_indices) < k and remaining_indices:
                best_score = -float('inf')
                best_idx = None
                
                for idx in remaining_indices:
                    # Relevance score (similarity to query)
                    relevance = np.dot(query_embedding, result_embeddings[idx])
                    
                    # Diversity score (minimum similarity to selected results)
                    diversity = float('inf')
                    for selected_idx in selected_indices:
                        similarity = np.dot(
                            result_embeddings[idx],
                            result_embeddings[selected_idx]
                        )
                        diversity = min(diversity, similarity)
                    
                    # MMR score
                    mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity
                    
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best_idx = idx
                
                if best_idx is not None:
                    selected_indices.append(best_idx)
                    remaining_indices.remove(best_idx)
                else:
                    break
            
            # Return selected results
            mmr_results = [results[i] for i in selected_indices]
            
            # Update method to indicate MMR was applied
            for result in mmr_results:
                result["method"] = RetrievalMethod.MMR.value
            
            return mmr_results
            
        except Exception as e:
            self.log_error("MMR application failed", error=e)
            return results[:k]  # Fallback to top-k
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Re-rank search results using cross-encoder model."""
        
        try:
            if not self._reranker_model or len(results) <= 1:
                return results
            
            # Prepare query-document pairs
            pairs = []
            for result in results:
                # Use document title + text for better context
                doc_text = result.get("text", "")
                if result.get("document_title"):
                    doc_text = f"{result['document_title']}: {doc_text}"
                
                pairs.append([query, doc_text[:512]])  # Truncate for efficiency
            
            # Get re-ranking scores
            rerank_scores = await asyncio.get_event_loop().run_in_executor(
                None,
                self._reranker_model.predict,
                pairs
            )
            
            # Update results with re-ranking scores
            for result, score in zip(results, rerank_scores):
                result["rerank_score"] = float(score)
                result["method"] = RetrievalMethod.RERANK.value
            
            # Sort by re-ranking score
            results.sort(key=lambda x: x["rerank_score"], reverse=True)
            
            return results
            
        except Exception as e:
            self.log_error("Re-ranking failed", error=e)
            return results
    
    async def _load_reranker_model(self):
        """Load cross-encoder re-ranking model."""
        
        try:
            if CrossEncoder is None:
                self.log_warning("CrossEncoder not available, skipping re-ranking model")
                return
                
            model_name = settings.RE_RANKING_MODEL
            
            self.log_info("Loading re-ranking model", model=model_name)
            
            # Load model in thread pool
            self._reranker_model = await asyncio.get_event_loop().run_in_executor(
                None,
                CrossEncoder,
                model_name
            )
            
            self.log_info("Re-ranking model loaded successfully")
            
        except Exception as e:
            self.log_error("Failed to load re-ranking model", error=e)
            # Continue without re-ranking
            self._reranker_model = None
    
    async def _get_chunk_data(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk data from database."""
        
        try:
            # Try cache first
            cache_key = f"chunk_data:{chunk_id}"
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                return cached_data
            
            # Get from database
            async with get_db_session() as session:
                query = (
                    select(Chunk)
                    .join(Document)
                    .options(joinedload(Chunk.document))
                    .where(Chunk.id == chunk_id)
                )
                
                result = await session.execute(query)
                chunk = result.scalar_one_or_none()
                
                if not chunk:
                    return None
                
                chunk_data = {
                    "text": chunk.text,
                    "tokens": chunk.tokens,
                    "chunk_type": chunk.chunk_type,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "quality_score": chunk.quality_score,
                    "document_id": str(chunk.document_id),
                    "document_title": chunk.document.title,
                    "document_url": chunk.document.url,
                    "source_id": str(chunk.document.source_id),
                }
                
                # Cache for future use
                await cache_service.set(cache_key, chunk_data, ttl=3600)
                
                return chunk_data
                
        except Exception as e:
            self.log_error("Failed to get chunk data", chunk_id=chunk_id, error=e)
            return None
    
    async def _calculate_lexical_score(self, query: str, text: str) -> float:
        """Calculate lexical similarity score between query and text."""
        
        # Simplified TF-IDF-like scoring
        query_terms = set(query.lower().split())
        text_terms = set(text.lower().split())
        
        if not query_terms:
            return 0.0
        
        # Jaccard similarity
        intersection = len(query_terms & text_terms)
        union = len(query_terms | text_terms)
        
        return intersection / union if union > 0 else 0.0
    
    async def _log_retrieval_events(
        self,
        query: str,
        results: List[Dict[str, Any]],
        user_id: Optional[str],
        tenant_id: str,
        language: str
    ):
        """Log retrieval events for analytics."""
        
        try:
            # Generate query ID for this search
            import uuid
            query_id = str(uuid.uuid4())
            
            # Create retrieval events
            events = []
            for rank, result in enumerate(results, 1):
                event = RetrievalEvent(
                    query_id=query_id,
                    user_id=user_id,
                    chunk_id=result["chunk_id"],
                    method=result["method"],
                    rank=rank,
                    score=result.get("hybrid_score", result.get("vector_score", 0.0)),
                    vector_score=result.get("vector_score"),
                    lexical_score=result.get("lexical_score"),
                    rerank_score=result.get("rerank_score"),
                    query_text=query,
                    query_language=language,
                    retrieval_time_ms=0,  # Would be calculated in calling function
                    total_candidates=len(results)
                )
                events.append(event)
            
            # Save events to database (in background)
            asyncio.create_task(self._save_retrieval_events(events))
            
        except Exception as e:
            self.log_error("Failed to log retrieval events", error=e)
    
    async def _save_retrieval_events(self, events: List[RetrievalEvent]):
        """Save retrieval events to database."""
        
        try:
            async with get_db_session() as session:
                session.add_all(events)
                await session.commit()
                
        except Exception as e:
            self.log_error("Failed to save retrieval events", error=e)


# Global search service instance
search_service = SearchService()