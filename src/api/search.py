"""Search and retrieval endpoints."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, Field
import asyncio

from ..core.database import get_db
from ..core.auth import get_current_active_user
from ..models.user import User
from ..models.document import Document, DocumentStatus
from ..models.chunk import Chunk
from ..services.search_service import SearchService, SearchType, SearchResult
from ..services.embedding_service import EmbeddingService
from ..services.rag_service import RAGService
from ..middleware.dependencies import get_search_service, get_embedding_service, get_rag_service
from ..core.config import settings

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    search_type: SearchType = SearchType.HYBRID
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_metadata: bool = True
    document_ids: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    rerank_results: bool = True


class SearchResultResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    score: float
    chunk_index: int
    metadata: Dict[str, Any]
    highlights: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultResponse]
    total_results: int
    search_type: str
    processing_time_ms: int
    suggestions: List[str] = Field(default_factory=list)


class RAGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    search_params: Optional[SearchRequest] = None
    model: Optional[str] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    include_sources: bool = True
    stream: bool = False


class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResultResponse]
    model_used: str
    processing_time_ms: int
    token_usage: Dict[str, int]
    confidence_score: float


@router.post("/", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    """Search through documents using hybrid search (vector + keyword)."""
    start_time = datetime.now()
    
    try:
        # Build document filter for user's tenant
        document_filter = {
            "tenant_id": current_user.tenant_id
        }
        
        # Add optional filters
        if search_request.document_ids:
            document_filter["document_ids"] = search_request.document_ids
        
        if search_request.categories:
            document_filter["categories"] = search_request.categories
        
        if search_request.date_from:
            document_filter["date_from"] = search_request.date_from
        
        if search_request.date_to:
            document_filter["date_to"] = search_request.date_to
        
        # Perform search
        search_results = await search_service.search(
            query=search_request.query,
            search_type=search_request.search_type,
            limit=search_request.limit,
            similarity_threshold=search_request.similarity_threshold,
            document_filter=document_filter,
            rerank=search_request.rerank_results
        )
        
        # Convert to response format
        response_results = []
        for result in search_results:
            # Get document info
            doc_query = select(Document).where(Document.id == result.document_id)
            doc_result = await db.execute(doc_query)
            document = doc_result.scalar_one_or_none()
            
            if document:
                response_results.append(SearchResultResponse(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    document_title=document.title,
                    content=result.content,
                    score=result.score,
                    chunk_index=result.chunk_index,
                    metadata=result.extra_metadata if search_request.include_metadata else {},
                    highlights=result.highlights or []
                ))
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Get search suggestions (basic implementation)
        suggestions = await _get_search_suggestions(search_request.query, current_user.tenant_id, db)
        
        return SearchResponse(
            query=search_request.query,
            results=response_results,
            total_results=len(response_results),
            search_type=search_request.search_type.value,
            processing_time_ms=processing_time,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/rag", response_model=RAGResponse)
async def rag_query(
    rag_request: RAGRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Perform RAG (Retrieval-Augmented Generation) query."""
    start_time = datetime.now()
    
    try:
        # Use provided search params or defaults
        search_params = rag_request.search_params or SearchRequest(
            query=rag_request.question,
            limit=5
        )
        
        # Build document filter
        document_filter = {
            "tenant_id": current_user.tenant_id
        }
        
        # Perform RAG
        rag_result = await rag_service.generate_answer(
            question=rag_request.question,
            search_params=search_params,
            document_filter=document_filter,
            model=rag_request.model or settings.DEFAULT_LLM_MODEL,
            temperature=rag_request.temperature,
            max_tokens=rag_request.max_tokens
        )
        
        # Convert sources to response format
        sources = []
        if rag_request.include_sources:
            for source in rag_result.sources:
                # Get document info
                doc_query = select(Document).where(Document.id == source.document_id)
                doc_result = await db.execute(doc_query)
                document = doc_result.scalar_one_or_none()
                
                if document:
                    sources.append(SearchResultResponse(
                        chunk_id=source.chunk_id,
                        document_id=source.document_id,
                        document_title=document.title,
                        content=source.content,
                        score=source.score,
                        chunk_index=source.chunk_index,
                        metadata=source.source_extra_metadata,
                        highlights=source.highlights or []
                    ))
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return RAGResponse(
            question=rag_request.question,
            answer=rag_result.answer,
            sources=sources,
            model_used=rag_result.model_used,
            processing_time_ms=processing_time,
            token_usage=rag_result.token_usage,
            confidence_score=rag_result.confidence_score
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get search query suggestions based on user's documents."""
    try:
        suggestions = await _get_search_suggestions(query, current_user.tenant_id, db, limit)
        
        return {
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/categories")
async def get_document_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available document categories for filtering."""
    try:
        # Get unique categories from user's documents
        query = select(Document.category).where(
            Document.tenant_id == current_user.tenant_id,
            Document.status == DocumentStatus.PROCESSED,
            Document.category.isnot(None)
        ).distinct()
        
        result = await db.execute(query)
        categories = [cat[0] for cat in result.fetchall() if cat[0]]
        
        return {
            "categories": sorted(categories)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.get("/tags")
async def get_document_tags(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available document tags for filtering."""
    try:
        # Get all tags from user's documents
        query = select(Document.tags).where(
            Document.tenant_id == current_user.tenant_id,
            Document.status == DocumentStatus.PROCESSED,
            Document.tags.isnot(None)
        )
        
        result = await db.execute(query)
        all_tags = set()
        
        for row in result.fetchall():
            if row[0]:  # tags is a list
                all_tags.update(row[0])
        
        return {
            "tags": sorted(list(all_tags))
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tags: {str(e)}"
        )


@router.get("/stats")
async def get_search_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get search and document statistics."""
    try:
        # Get document stats
        doc_stats_query = select([
            func.count(Document.id).label('total_documents'),
            func.count().filter(Document.status == DocumentStatus.PROCESSED).label('processed_documents'),
            func.sum(Document.processed_chunks).label('total_chunks'),
            func.avg(Document.file_size).label('avg_file_size')
        ]).where(
            Document.tenant_id == current_user.tenant_id
        )
        
        doc_stats_result = await db.execute(doc_stats_query)
        doc_stats = doc_stats_result.fetchone()
        
        # Get chunk stats
        chunk_stats_query = select([
            func.count(Chunk.id).label('total_chunks'),
            func.avg(func.length(Chunk.content)).label('avg_chunk_length')
        ]).join(Document).where(
            Document.tenant_id == current_user.tenant_id
        )
        
        chunk_stats_result = await db.execute(chunk_stats_query)
        chunk_stats = chunk_stats_result.fetchone()
        
        return {
            "documents": {
                "total": doc_stats.total_documents or 0,
                "processed": doc_stats.processed_documents or 0,
                "processing_rate": (
                    (doc_stats.processed_documents / doc_stats.total_documents * 100) 
                    if doc_stats.total_documents > 0 else 0
                ),
                "avg_file_size_mb": round((doc_stats.avg_file_size or 0) / (1024 * 1024), 2)
            },
            "chunks": {
                "total": chunk_stats.total_chunks or 0,
                "avg_length": int(chunk_stats.avg_chunk_length or 0)
            },
            "search_ready": (doc_stats.processed_documents or 0) > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search stats: {str(e)}"
        )


@router.post("/similar/{chunk_id}")
async def find_similar_chunks(
    chunk_id: str,
    limit: int = Query(10, ge=1, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    search_service: SearchService = Depends(get_search_service)
):
    """Find chunks similar to a given chunk."""
    try:
        # Verify chunk access
        chunk_query = select(Chunk).join(Document).where(
            Chunk.id == chunk_id,
            Document.tenant_id == current_user.tenant_id
        )
        
        chunk_result = await db.execute(chunk_query)
        chunk = chunk_result.scalar_one_or_none()
        
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found"
            )
        
        # Find similar chunks
        similar_chunks = await search_service.find_similar_chunks(
            chunk_id=chunk_id,
            limit=limit,
            similarity_threshold=similarity_threshold,
            tenant_id=current_user.tenant_id
        )
        
        # Convert to response format
        results = []
        for similar_chunk in similar_chunks:
            # Get document info
            doc_query = select(Document).where(Document.id == similar_chunk.document_id)
            doc_result = await db.execute(doc_query)
            document = doc_result.scalar_one_or_none()
            
            if document:
                results.append(SearchResultResponse(
                    chunk_id=similar_chunk.chunk_id,
                    document_id=similar_chunk.document_id,
                    document_title=document.title,
                    content=similar_chunk.content,
                    score=similar_chunk.score,
                    chunk_index=similar_chunk.chunk_index,
                    metadata=similar_chunk.extra_metadata,
                    highlights=[]
                ))
        
        return {
            "source_chunk_id": chunk_id,
            "similar_chunks": results,
            "total_found": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar chunks: {str(e)}"
        )


async def _get_search_suggestions(
    query: str, 
    tenant_id: str, 
    db: AsyncSession, 
    limit: int = 5
) -> List[str]:
    """Get search suggestions based on document content and previous searches."""
    try:
        # Simple implementation: get related terms from document titles and content
        suggestions = []
        
        # Get document titles that contain similar words
        title_query = select(Document.title).where(
            Document.tenant_id == tenant_id,
            Document.status == DocumentStatus.PROCESSED,
            Document.title.ilike(f"%{query}%")
        ).limit(limit)
        
        title_result = await db.execute(title_query)
        titles = [title[0] for title in title_result.fetchall()]
        
        # Extract meaningful terms from titles
        for title in titles:
            words = title.lower().split()
            for word in words:
                if len(word) > 3 and word not in suggestions and query.lower() in word.lower():
                    suggestions.append(word)
                    if len(suggestions) >= limit:
                        break
            if len(suggestions) >= limit:
                break
        
        return suggestions[:limit]
        
    except Exception:
        return []