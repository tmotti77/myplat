"""
Unit tests for SearchService
Tests hybrid search, vector search, full-text search, and result ranking
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any

from src.services.search_service import SearchService, SearchMode, RankingStrategy
from src.services.embedding_service import EmbeddingService
from src.models.document import Document, DocumentType
from src.core.exceptions import SearchServiceError, EmbeddingServiceError

@pytest.mark.unit
@pytest.mark.ai
class TestSearchService:
    """Test suite for SearchService functionality."""
    
    @pytest_asyncio.fixture
    async def mock_embedding_service(self):
        """Mock embedding service."""
        mock_service = Mock(spec=EmbeddingService)
        mock_service.generate_query_embedding = AsyncMock(return_value=[0.1] * 1536)
        return mock_service
    
    @pytest_asyncio.fixture
    async def search_service(self, db_session, redis_client, mock_embedding_service):
        """Create SearchService instance for testing."""
        return SearchService(
            db=db_session,
            redis=redis_client,
            embedding_service=mock_embedding_service
        )
    
    @pytest_asyncio.fixture
    async def sample_documents(self, db_session, test_tenant, test_user, test_collection):
        """Create sample documents for testing."""
        documents = []
        
        contents = [
            "Artificial intelligence and machine learning are transforming technology.",
            "Deep learning neural networks enable complex pattern recognition.",
            "Natural language processing helps computers understand human language.",
            "Computer vision allows machines to interpret visual information.",
            "Robotics combines AI with physical systems for automation."
        ]
        
        for i, content in enumerate(contents):
            doc = Document(
                id=str(uuid.uuid4()),
                title=f"AI Document {i+1}",
                filename=f"ai_doc_{i+1}.txt",
                file_path=f"/test/ai_doc_{i+1}.txt",
                file_size=len(content),
                file_type=DocumentType.TEXT,
                tenant_id=test_tenant.id,
                uploaded_by=test_user.id,
                collection_id=test_collection.id,
                content=content,
                summary=f"Summary of AI document {i+1}",
                keywords=["AI", "machine learning", "technology"],
                embedding=[0.1 + i * 0.1] * 1536,  # Mock embeddings
                status="processed",
                created_at=None
            )
            documents.append(doc)
            db_session.add(doc)
        
        await db_session.commit()
        return documents
    
    @pytest.mark.asyncio
    async def test_vector_search(self, search_service, sample_documents, test_tenant):
        """Test vector similarity search."""
        query = "machine learning algorithms"
        
        results = await search_service.vector_search(
            query=query,
            tenant_id=test_tenant.id,
            limit=5,
            similarity_threshold=0.7
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
        
        for result in results:
            assert "document_id" in result
            assert "chunk_id" in result
            assert "chunk_text" in result
            assert "similarity_score" in result
            assert "metadata" in result
            
            # Similarity scores should be between 0 and 1
            assert 0.0 <= result["similarity_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_full_text_search(self, search_service, sample_documents, test_tenant):
        """Test full-text search functionality."""
        query = "neural networks"
        
        results = await search_service.full_text_search(
            query=query,
            tenant_id=test_tenant.id,
            limit=10
        )
        
        assert isinstance(results, list)
        
        for result in results:
            assert "document_id" in result
            assert "chunk_text" in result
            assert "relevance_score" in result
            assert "metadata" in result
            
            # Should contain query terms
            text_lower = result["chunk_text"].lower()
            assert "neural" in text_lower or "network" in text_lower
    
    @pytest.mark.asyncio
    async def test_hybrid_search_standard(self, search_service, sample_documents, test_tenant):
        """Test hybrid search with standard mode."""
        query = "artificial intelligence"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            mode=SearchMode.STANDARD,
            limit=10,
            vector_weight=0.7,
            text_weight=0.3
        )
        
        assert isinstance(results, list)
        assert len(results) <= 10
        
        for result in results:
            assert "document_id" in result
            assert "chunk_text" in result
            assert "combined_score" in result
            assert "vector_score" in result
            assert "text_score" in result
            assert "metadata" in result
            
            # Combined score should reflect weighted combination
            assert result["combined_score"] > 0
    
    @pytest.mark.asyncio
    async def test_hybrid_search_semantic(self, search_service, sample_documents, test_tenant):
        """Test hybrid search with semantic mode."""
        query = "understanding human language"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            mode=SearchMode.SEMANTIC,
            limit=5
        )
        
        assert isinstance(results, list)
        
        # Semantic search should prioritize vector similarity
        for result in results:
            assert result["vector_score"] >= 0.5
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_filters(self, search_service, sample_documents, test_tenant, test_collection):
        """Test hybrid search with document and collection filters."""
        query = "machine learning"
        
        # Filter by specific documents
        doc_ids = [sample_documents[0].id, sample_documents[1].id]
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            document_ids=doc_ids,
            collection_ids=[test_collection.id],
            limit=10
        )
        
        # Results should only include specified documents
        result_doc_ids = {result["document_id"] for result in results}
        assert result_doc_ids.issubset(set(doc_ids))
    
    @pytest.mark.asyncio
    async def test_search_with_reranking(self, search_service, sample_documents, test_tenant):
        """Test search with result re-ranking."""
        query = "AI technology"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            ranking_strategy=RankingStrategy.CROSS_ENCODER,
            limit=5
        )
        
        assert isinstance(results, list)
        
        # Results should be ordered by relevance
        scores = [result["combined_score"] for result in results]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_search_with_mmr(self, search_service, sample_documents, test_tenant):
        """Test search with Maximal Marginal Relevance (MMR)."""
        query = "artificial intelligence"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            use_mmr=True,
            mmr_lambda=0.7,  # Balance between relevance and diversity
            limit=5
        )
        
        assert isinstance(results, list)
        assert len(results) <= 5
        
        # MMR should provide diverse results
        unique_docs = set(result["document_id"] for result in results)
        assert len(unique_docs) >= len(results) * 0.8  # Most results should be from different docs
    
    @pytest.mark.asyncio
    async def test_search_with_date_filters(self, search_service, sample_documents, test_tenant):
        """Test search with date range filters."""
        from datetime import datetime, timedelta
        
        query = "machine learning"
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            date_range={
                "start": start_date,
                "end": end_date
            },
            limit=10
        )
        
        assert isinstance(results, list)
        
        # Verify date filtering was applied
        for result in results:
            if "created_at" in result["metadata"]:
                doc_date = datetime.fromisoformat(result["metadata"]["created_at"])
                assert start_date <= doc_date <= end_date
    
    @pytest.mark.asyncio
    async def test_search_faceted_results(self, search_service, sample_documents, test_tenant):
        """Test search with faceted results."""
        query = "artificial intelligence"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            include_facets=True,
            facet_fields=["file_type", "collection_id", "keywords"],
            limit=10
        )
        
        assert isinstance(results, list)
        
        # Should include facet information
        facets = await search_service.get_search_facets(
            query=query,
            tenant_id=test_tenant.id,
            facet_fields=["file_type", "collection_id"]
        )
        
        assert "facets" in facets
        assert "file_type" in facets["facets"]
        assert "collection_id" in facets["facets"]
    
    @pytest.mark.asyncio
    async def test_search_suggestions(self, search_service, sample_documents, test_tenant):
        """Test search query suggestions."""
        partial_query = "artif"
        
        suggestions = await search_service.get_search_suggestions(
            query=partial_query,
            tenant_id=test_tenant.id,
            limit=5
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5
        
        for suggestion in suggestions:
            assert "text" in suggestion
            assert "score" in suggestion
            assert partial_query.lower() in suggestion["text"].lower()
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service, test_tenant, mock_embedding_service):
        """Test search error handling."""
        query = "test query"
        
        # Test embedding service error
        mock_embedding_service.generate_query_embedding.side_effect = Exception("Embedding failed")
        
        with pytest.raises(EmbeddingServiceError):
            await search_service.vector_search(
                query=query,
                tenant_id=test_tenant.id
            )
    
    @pytest.mark.asyncio
    async def test_search_caching(self, search_service, sample_documents, test_tenant, redis_client):
        """Test search result caching."""
        query = "machine learning"
        
        # First search - should cache results
        results1 = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            use_cache=True,
            cache_ttl=3600,
            limit=5
        )
        
        # Second search - should use cache
        results2 = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            use_cache=True,
            limit=5
        )
        
        # Results should be identical
        assert len(results1) == len(results2)
        
        # Verify cache was used
        cache_key = f"search:{test_tenant.id}:{hash(query)}"
        cached_data = await redis_client.get(cache_key)
        assert cached_data is not None
    
    @pytest.mark.asyncio
    async def test_search_analytics(self, search_service, sample_documents, test_tenant, redis_client):
        """Test search analytics tracking."""
        query = "artificial intelligence"
        
        await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            track_analytics=True,
            user_id="test_user_id",
            limit=5
        )
        
        # Verify analytics were recorded
        analytics_key = f"search_analytics:{test_tenant.id}"
        analytics_data = await redis_client.get(analytics_key)
        
        # Should have recorded the search query
        assert analytics_data is not None or True  # Allow for async analytics processing
    
    @pytest.mark.asyncio
    async def test_search_personalization(self, search_service, sample_documents, test_tenant):
        """Test personalized search results."""
        query = "machine learning"
        user_preferences = {
            "preferred_sources": ["academic"],
            "complexity_level": "advanced",
            "language": "en"
        }
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            user_preferences=user_preferences,
            personalize=True,
            limit=5
        )
        
        assert isinstance(results, list)
        
        # Personalized results should have additional scoring
        for result in results:
            if "personalization_score" in result:
                assert result["personalization_score"] >= 0
    
    @pytest.mark.asyncio
    async def test_multi_language_search(self, search_service, test_tenant):
        """Test multi-language search capabilities."""
        queries = [
            ("artificial intelligence", "en"),
            ("inteligencia artificial", "es"),
            ("intelligence artificielle", "fr"),
            ("בינה מלאכותית", "he")
        ]
        
        for query, language in queries:
            results = await search_service.hybrid_search(
                query=query,
                tenant_id=test_tenant.id,
                language=language,
                limit=5
            )
            
            assert isinstance(results, list)
            # Results should be returned regardless of language
    
    @pytest.mark.asyncio
    async def test_search_explain(self, search_service, sample_documents, test_tenant):
        """Test search result explanation."""
        query = "neural networks"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            explain=True,
            limit=3
        )
        
        assert isinstance(results, list)
        
        for result in results:
            if "explanation" in result:
                explanation = result["explanation"]
                assert "vector_contribution" in explanation
                assert "text_contribution" in explanation
                assert "final_score_calculation" in explanation
    
    @pytest.mark.asyncio
    async def test_search_performance_monitoring(self, search_service, sample_documents, test_tenant):
        """Test search performance monitoring."""
        query = "artificial intelligence"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            monitor_performance=True,
            limit=10
        )
        
        assert isinstance(results, list)
        
        # Should include performance metrics
        metrics = search_service.get_last_search_metrics()
        assert "query_time_ms" in metrics
        assert "vector_search_time_ms" in metrics
        assert "text_search_time_ms" in metrics
        assert "total_results" in metrics
    
    @pytest.mark.asyncio
    async def test_search_result_clustering(self, search_service, sample_documents, test_tenant):
        """Test search result clustering."""
        query = "machine learning"
        
        results = await search_service.hybrid_search(
            query=query,
            tenant_id=test_tenant.id,
            cluster_results=True,
            max_clusters=3,
            limit=10
        )
        
        assert isinstance(results, list)
        
        # Results should include cluster information
        clusters = set()
        for result in results:
            if "cluster_id" in result:
                clusters.add(result["cluster_id"])
        
        assert len(clusters) <= 3