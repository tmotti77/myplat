"""Search service implementing hybrid search with PostgreSQL."""

import asyncio
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, or_
from sqlalchemy.orm import selectinload

from ..core.database import get_db_session
from ..core.logging import get_logger, LoggerMixin
from ..models.document import Document, DocumentStatus
from ..models.chunk import Chunk
from ..services.embedding_service import embedding_service

logger = get_logger(__name__)


class SearchType(str, Enum):
    """Search types supported by the system."""
    SEMANTIC = "semantic"      # Vector similarity search
    KEYWORD = "keyword"        # Full-text search
    HYBRID = "hybrid"          # Combination of both


@dataclass
class SearchResult:
    """Individual search result."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    chunk_index: int
    metadata: Dict[str, Any]
    highlights: Optional[List[str]] = None


class SearchService(LoggerMixin):
    """Service for document search using hybrid approach."""
    
    def __init__(self):
        self.default_k = 10
        self.semantic_weight = 0.6  # Weight for semantic search
        self.keyword_weight = 0.4   # Weight for keyword search
    
    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.HYBRID,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        document_filter: Optional[Dict[str, Any]] = None,
        rerank: bool = True
    ) -> List[SearchResult]:
        """Perform search with specified type."""
        
        try:
            if search_type == SearchType.SEMANTIC:
                return await self._semantic_search(
                    query, limit, similarity_threshold, document_filter
                )
            elif search_type == SearchType.KEYWORD:
                return await self._keyword_search(
                    query, limit, document_filter
                )
            else:  # HYBRID
                return await self._hybrid_search(
                    query, limit, similarity_threshold, document_filter, rerank
                )
                
        except Exception as e:
            self.log_error("Search failed", query=query[:100], search_type=search_type, error=e)
            raise
    
    async def _semantic_search(
        self,
        query: str,
        limit: int,
        similarity_threshold: float,
        document_filter: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Perform semantic search using embeddings."""
        
        try:
            # Generate query embedding
            query_embedding = await embedding_service.generate_embeddings(query)
            
            async with get_db_session() as session:
                # Build base query
                query_stmt = (
                    select(Chunk, Document)
                    .join(Document, Chunk.document_id == Document.id)
                    .where(Document.status == DocumentStatus.PROCESSED)
                )
                
                # Apply document filters
                query_stmt = self._apply_filters(query_stmt, document_filter)
                
                # For PostgreSQL with pgvector, we would use vector similarity
                # This is a simplified implementation using basic similarity
                result = await session.execute(query_stmt)
                chunks_and_docs = result.fetchall()
                
                # Calculate similarities (simplified - in production use pgvector)
                results = []
                for chunk, document in chunks_and_docs:
                    if chunk.embedding_id:  # Has embedding
                        # Simplified similarity calculation
                        # In production, use pgvector's <-> operator
                        similarity = await self._calculate_similarity(query_embedding, chunk)
                        
                        if similarity >= similarity_threshold:
                            results.append(SearchResult(
                                chunk_id=chunk.id,
                                document_id=document.id,
                                content=chunk.content,
                                score=similarity,
                                chunk_index=chunk.chunk_index,
                                metadata={
                                    "document_title": document.title,
                                    "document_filename": document.filename,
                                    "document_category": document.category,
                                    "document_tags": document.tags or [],
                                    "search_type": "semantic"
                                }
                            ))
                
                # Sort by score and limit
                results.sort(key=lambda x: x.score, reverse=True)
                return results[:limit]
                
        except Exception as e:
            self.log_error("Semantic search failed", query=query[:100], error=e)
            raise
    
    async def _keyword_search(
        self,
        query: str,
        limit: int,
        document_filter: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Perform keyword search using PostgreSQL full-text search."""
        
        try:
            async with get_db_session() as session:
                # Prepare full-text search query
                search_query = self._prepare_fulltext_query(query)
                
                # Build query with full-text search
                query_stmt = (
                    select(
                        Chunk,
                        Document,
                        func.ts_rank(
                            func.to_tsvector('english', Chunk.content),
                            func.plainto_tsquery('english', search_query)
                        ).label('rank')
                    )
                    .join(Document, Chunk.document_id == Document.id)
                    .where(
                        and_(
                            Document.status == DocumentStatus.PROCESSED,
                            func.to_tsvector('english', Chunk.content).match(
                                func.plainto_tsquery('english', search_query)
                            )
                        )
                    )
                    .order_by(text('rank DESC'))
                    .limit(limit)
                )
                
                # Apply document filters
                query_stmt = self._apply_filters(query_stmt, document_filter)
                
                result = await session.execute(query_stmt)
                chunks_docs_ranks = result.fetchall()
                
                results = []
                for chunk, document, rank in chunks_docs_ranks:
                    results.append(SearchResult(
                        chunk_id=chunk.id,
                        document_id=document.id,
                        content=chunk.content,
                        score=float(rank) if rank else 0.0,
                        chunk_index=chunk.chunk_index,
                        metadata={
                            "document_title": document.title,
                            "document_filename": document.filename,
                            "document_category": document.category,
                            "document_tags": document.tags or [],
                            "search_type": "keyword"
                        },
                        highlights=self._extract_highlights(chunk.content, query)
                    ))
                
                return results
                
        except Exception as e:
            self.log_error("Keyword search failed", query=query[:100], error=e)
            raise
    
    async def _hybrid_search(
        self,
        query: str,
        limit: int,
        similarity_threshold: float,
        document_filter: Optional[Dict[str, Any]],
        rerank: bool
    ) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search."""
        
        try:
            # Perform both searches in parallel
            semantic_task = self._semantic_search(query, limit * 2, similarity_threshold, document_filter)
            keyword_task = self._keyword_search(query, limit * 2, document_filter)
            
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(semantic_results, Exception):
                self.log_warning("Semantic search failed in hybrid", error=semantic_results)
                semantic_results = []
            
            if isinstance(keyword_results, Exception):
                self.log_warning("Keyword search failed in hybrid", error=keyword_results)
                keyword_results = []
            
            # Combine and normalize scores
            combined_results = self._combine_search_results(
                semantic_results, keyword_results, query
            )
            
            # Sort by combined score
            combined_results.sort(key=lambda x: x.score, reverse=True)
            
            # Apply reranking if requested
            if rerank and len(combined_results) > limit:
                combined_results = await self._rerank_results(query, combined_results[:limit * 2])
            
            return combined_results[:limit]
            
        except Exception as e:
            self.log_error("Hybrid search failed", query=query[:100], error=e)
            raise
    
    def _combine_search_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Combine results from semantic and keyword search."""
        
        # Create lookup for semantic results
        semantic_lookup = {r.chunk_id: r for r in semantic_results}
        keyword_lookup = {r.chunk_id: r for r in keyword_results}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(semantic_lookup.keys()) | set(keyword_lookup.keys())
        
        combined_results = []
        
        for chunk_id in all_chunk_ids:
            semantic_result = semantic_lookup.get(chunk_id)
            keyword_result = keyword_lookup.get(chunk_id)
            
            # Calculate combined score
            semantic_score = semantic_result.score if semantic_result else 0.0
            keyword_score = keyword_result.score if keyword_result else 0.0
            
            # Normalize scores (simple approach)
            normalized_semantic = min(semantic_score, 1.0)
            normalized_keyword = min(keyword_score / 1.0, 1.0)  # Assuming max keyword score is 1.0
            
            combined_score = (
                normalized_semantic * self.semantic_weight +
                normalized_keyword * self.keyword_weight
            )
            
            # Use the result with content (prefer semantic if both exist)
            base_result = semantic_result or keyword_result
            
            # Create combined result
            combined_result = SearchResult(
                chunk_id=chunk_id,
                document_id=base_result.document_id,
                content=base_result.content,
                score=combined_score,
                chunk_index=base_result.chunk_index,
                metadata={
                    **base_result.extra_metadata,
                    "search_type": "hybrid",
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "has_semantic": semantic_result is not None,
                    "has_keyword": keyword_result is not None
                },
                highlights=keyword_result.highlights if keyword_result else None
            )
            
            combined_results.append(combined_result)
        
        return combined_results
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Rerank results using additional criteria."""
        
        # Simple reranking based on query term frequency and document quality
        for result in results:
            query_terms = query.lower().split()
            content_lower = result.content.lower()
            
            # Calculate term frequency boost
            term_matches = sum(1 for term in query_terms if term in content_lower)
            term_frequency_boost = term_matches / len(query_terms) * 0.1
            
            # Calculate length penalty for very short or very long chunks
            length_penalty = 0.0
            if len(result.content) < 100:
                length_penalty = -0.1
            elif len(result.content) > 2000:
                length_penalty = -0.05
            
            # Apply adjustments
            result.score += term_frequency_boost + length_penalty
            result.score = max(0.0, min(1.0, result.score))  # Clamp to [0, 1]
        
        return results
    
    def _apply_filters(self, query_stmt, document_filter: Optional[Dict[str, Any]]):
        """Apply document filters to the query."""
        
        if not document_filter:
            return query_stmt
        
        # Tenant filter
        if "tenant_id" in document_filter:
            query_stmt = query_stmt.where(Document.tenant_id == document_filter["tenant_id"])
        
        # Document IDs filter
        if "document_ids" in document_filter:
            query_stmt = query_stmt.where(Document.id.in_(document_filter["document_ids"]))
        
        # Category filter
        if "categories" in document_filter:
            query_stmt = query_stmt.where(Document.category.in_(document_filter["categories"]))
        
        # Date filters
        if "date_from" in document_filter:
            query_stmt = query_stmt.where(Document.upload_date >= document_filter["date_from"])
        
        if "date_to" in document_filter:
            query_stmt = query_stmt.where(Document.upload_date <= document_filter["date_to"])
        
        return query_stmt
    
    def _prepare_fulltext_query(self, query: str) -> str:
        """Prepare query for PostgreSQL full-text search."""
        
        # Clean and prepare the query
        # Remove special characters and prepare for tsquery
        cleaned_query = ' '.join(query.split())
        
        # Simple query preparation (can be enhanced)
        return cleaned_query
    
    def _extract_highlights(self, content: str, query: str) -> List[str]:
        """Extract highlighted snippets from content."""
        
        query_terms = query.lower().split()
        content_lower = content.lower()
        highlights = []
        
        for term in query_terms:
            if term in content_lower:
                # Find position of term
                pos = content_lower.find(term)
                if pos >= 0:
                    # Extract snippet around the term
                    start = max(0, pos - 50)
                    end = min(len(content), pos + len(term) + 50)
                    snippet = content[start:end]
                    
                    # Add ellipsis if needed
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(content):
                        snippet = snippet + "..."
                    
                    highlights.append(snippet)
        
        return highlights[:3]  # Limit to 3 highlights
    
    async def _calculate_similarity(self, query_embedding: List[float], chunk: Chunk) -> float:
        """Calculate similarity between query and chunk (simplified)."""
        
        # This is a simplified implementation
        # In production, you would:
        # 1. Store actual embeddings in the database or vector store
        # 2. Use pgvector for efficient similarity calculation
        # 3. Or use a dedicated vector database like Qdrant
        
        # For now, return a mock similarity based on basic text matching
        if not chunk.content:
            return 0.0
        
        # Simple text-based similarity as fallback
        # This should be replaced with actual vector similarity
        return 0.7  # Mock similarity score
    
    async def find_similar_chunks(
        self,
        chunk_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        tenant_id: Optional[str] = None
    ) -> List[SearchResult]:
        """Find chunks similar to a given chunk."""
        
        try:
            async with get_db_session() as session:
                # Get the source chunk
                source_chunk = await session.get(Chunk, chunk_id)
                if not source_chunk:
                    return []
                
                # Use the chunk content as query for similarity search
                return await self._semantic_search(
                    source_chunk.content,
                    limit,
                    similarity_threshold,
                    {"tenant_id": tenant_id} if tenant_id else None
                )
                
        except Exception as e:
            self.log_error("Similar chunks search failed", chunk_id=chunk_id, error=e)
            return []
    
    async def get_search_suggestions(
        self,
        partial_query: str,
        tenant_id: str,
        limit: int = 5
    ) -> List[str]:
        """Get search suggestions based on document content."""
        
        try:
            async with get_db_session() as session:
                # Simple implementation: get document titles that match
                query_stmt = (
                    select(Document.title)
                    .where(
                        and_(
                            Document.tenant_id == tenant_id,
                            Document.status == DocumentStatus.PROCESSED,
                            Document.title.ilike(f"%{partial_query}%")
                        )
                    )
                    .limit(limit)
                )
                
                result = await session.execute(query_stmt)
                titles = [row[0] for row in result.fetchall()]
                
                return titles
                
        except Exception as e:
            self.log_error("Search suggestions failed", query=partial_query, error=e)
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check search service health."""
        
        health = {
            "status": "healthy",
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "embedding_service": False
        }
        
        try:
            # Test embedding service
            test_embedding = await embedding_service.generate_embeddings("test")
            health["embedding_service"] = len(test_embedding) > 0
            
            # Test database connection
            async with get_db_session() as session:
                await session.execute(select(1))
                health["database"] = True
                
        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)
        
        return health


# Global search service instance  
search_service = SearchService()