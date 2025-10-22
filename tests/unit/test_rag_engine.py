"""
Unit tests for RAGEngine
Tests retrieval-augmented generation functionality, citation handling, and conversation management
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid
from typing import List, Dict, Any

from src.services.rag_engine import RAGEngine, RAGMode, ConversationMode
from src.services.search_service import SearchService
from src.services.llm_router import LLMRouter
from src.services.personalization import PersonalizationEngine
from src.models.user import User
from src.models.document import Document
from src.models.citation import Citation
from src.models.conversation import Conversation, ConversationMessage
from src.core.exceptions import (
    RAGProcessingError,
    InsufficientContextError,
    LLMServiceError,
    SearchServiceError
)

@pytest.mark.unit
@pytest.mark.ai
class TestRAGEngine:
    """Test suite for RAGEngine functionality."""
    
    @pytest_asyncio.fixture
    async def mock_search_service(self):
        """Mock search service."""
        mock_service = Mock(spec=SearchService)
        mock_service.hybrid_search = AsyncMock(return_value=[
            {
                "document_id": "doc_1",
                "chunk_id": "chunk_1",
                "chunk_text": "This is a test chunk about artificial intelligence and machine learning.",
                "source_title": "AI Research Paper",
                "source_type": "academic",
                "confidence": 0.95,
                "metadata": {
                    "page": 5,
                    "section": "Introduction",
                    "author": "Dr. Smith"
                }
            },
            {
                "document_id": "doc_2", 
                "chunk_id": "chunk_2",
                "chunk_text": "Machine learning algorithms can be categorized into supervised and unsupervised learning.",
                "source_title": "ML Handbook",
                "source_type": "textbook",
                "confidence": 0.88,
                "metadata": {
                    "page": 12,
                    "chapter": "Fundamentals"
                }
            }
        ])
        return mock_service
    
    @pytest_asyncio.fixture
    async def mock_llm_router(self):
        """Mock LLM router."""
        mock_router = Mock(spec=LLMRouter)
        mock_router.route_request = AsyncMock(return_value={
            "provider": "openai",
            "model": "gpt-4",
            "response": "Based on the provided context, artificial intelligence (AI) and machine learning (ML) are closely related fields. Machine learning is a subset of AI that focuses on algorithms that can learn from and make predictions on data.",
            "cost": 0.002,
            "latency": 1.2,
            "usage": {
                "prompt_tokens": 150,
                "completion_tokens": 75,
                "total_tokens": 225
            }
        })
        return mock_router
    
    @pytest_asyncio.fixture
    async def mock_personalization(self):
        """Mock personalization engine."""
        mock_engine = Mock(spec=PersonalizationEngine)
        mock_engine.personalize_search_results = AsyncMock(
            side_effect=lambda results, *args, **kwargs: results
        )
        mock_engine.get_user_preferences = AsyncMock(return_value={
            "preferred_sources": ["academic", "documentation"],
            "complexity_level": "advanced",
            "language": "en"
        })
        return mock_engine
    
    @pytest_asyncio.fixture
    async def rag_engine(self, db_session, redis_client, mock_search_service, 
                        mock_llm_router, mock_personalization):
        """Create RAGEngine instance for testing."""
        return RAGEngine(
            db=db_session,
            redis=redis_client,
            search_service=mock_search_service,
            llm_router=mock_llm_router,
            personalization_engine=mock_personalization
        )
    
    @pytest.mark.asyncio
    async def test_ask_question_standard_mode(self, rag_engine, test_user, test_tenant):
        """Test asking a question in standard RAG mode."""
        question = "What is artificial intelligence?"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            mode=RAGMode.STANDARD
        )
        
        assert "answer" in result
        assert "citations" in result
        assert "confidence" in result
        assert "conversation_id" in result
        
        assert result["confidence"] > 0.0
        assert len(result["citations"]) > 0
        assert "artificial intelligence" in result["answer"].lower()
        
        # Verify citations structure
        citation = result["citations"][0]
        assert "chunk_text" in citation
        assert "source_title" in citation
        assert "confidence" in citation
    
    @pytest.mark.asyncio
    async def test_ask_question_conversational_mode(self, rag_engine, test_user, test_tenant, db_session):
        """Test asking questions in conversational mode."""
        # Create initial conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            title="AI Discussion",
            mode=ConversationMode.CHAT,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(conversation)
        await db_session.commit()
        
        # Add previous message
        prev_message = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content="What is machine learning?",
            created_at=datetime.utcnow()
        )
        db_session.add(prev_message)
        await db_session.commit()
        
        # Ask follow-up question
        result = await rag_engine.ask_question(
            question="How is it different from AI?",
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            conversation_id=conversation.id,
            mode=RAGMode.CONVERSATIONAL
        )
        
        assert "answer" in result
        assert "conversation_id" in result
        assert result["conversation_id"] == conversation.id
    
    @pytest.mark.asyncio
    async def test_ask_question_research_mode(self, rag_engine, test_user, test_tenant):
        """Test asking a question in research mode."""
        question = "Provide a comprehensive analysis of machine learning algorithms"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            mode=RAGMode.RESEARCH,
            max_citations=10,
            include_metadata=True
        )
        
        assert "answer" in result
        assert "citations" in result
        assert "research_depth" in result
        assert "methodology" in result
        
        # Research mode should provide more detailed citations
        for citation in result["citations"]:
            assert "metadata" in citation
            assert citation["confidence"] >= 0.7  # Higher confidence threshold for research
    
    @pytest.mark.asyncio
    async def test_ask_question_summarization_mode(self, rag_engine, test_user, test_tenant):
        """Test asking a question in summarization mode."""
        question = "Summarize the key concepts of artificial intelligence"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            mode=RAGMode.SUMMARIZATION,
            document_ids=["doc_1", "doc_2"]
        )
        
        assert "answer" in result
        assert "summary_type" in result
        assert "key_points" in result
        assert len(result["key_points"]) > 0
    
    @pytest.mark.asyncio
    async def test_ask_question_comparison_mode(self, rag_engine, test_user, test_tenant):
        """Test asking a question in comparison mode."""
        question = "Compare supervised and unsupervised learning"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            mode=RAGMode.COMPARISON
        )
        
        assert "answer" in result
        assert "comparison_table" in result
        assert "similarities" in result
        assert "differences" in result
    
    @pytest.mark.asyncio
    async def test_ask_question_fact_check_mode(self, rag_engine, test_user, test_tenant):
        """Test asking a question in fact-checking mode."""
        question = "Machine learning was invented in 2020"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            mode=RAGMode.FACT_CHECK
        )
        
        assert "answer" in result
        assert "fact_check_result" in result
        assert "evidence" in result
        assert "confidence_score" in result
        
        # Should detect this as false
        assert result["fact_check_result"]["verdict"] == "false"
    
    @pytest.mark.asyncio
    async def test_ask_question_with_document_filter(self, rag_engine, test_user, test_tenant, mock_search_service):
        """Test asking a question with document filters."""
        question = "What is machine learning?"
        document_ids = ["doc_1"]
        
        await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            document_ids=document_ids,
            collection_ids=None
        )
        
        # Verify search service was called with document filter
        mock_search_service.hybrid_search.assert_called_once()
        call_args = mock_search_service.hybrid_search.call_args
        assert call_args[1]["document_ids"] == document_ids
    
    @pytest.mark.asyncio
    async def test_ask_question_with_collection_filter(self, rag_engine, test_user, test_tenant, 
                                                      test_collection, mock_search_service):
        """Test asking a question with collection filters."""
        question = "What is artificial intelligence?"
        collection_ids = [test_collection.id]
        
        await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            collection_ids=collection_ids
        )
        
        # Verify search service was called with collection filter
        mock_search_service.hybrid_search.assert_called_once()
        call_args = mock_search_service.hybrid_search.call_args
        assert call_args[1]["collection_ids"] == collection_ids
    
    @pytest.mark.asyncio
    async def test_ask_question_no_results(self, rag_engine, test_user, test_tenant, mock_search_service):
        """Test asking a question when no search results are found."""
        mock_search_service.hybrid_search.return_value = []
        
        with pytest.raises(InsufficientContextError):
            await rag_engine.ask_question(
                question="What is quantum computing?",
                tenant_id=test_tenant.id,
                user_id=test_user.id
            )
    
    @pytest.mark.asyncio
    async def test_ask_question_llm_error(self, rag_engine, test_user, test_tenant, mock_llm_router):
        """Test handling LLM service errors."""
        mock_llm_router.route_request.side_effect = Exception("LLM service unavailable")
        
        with pytest.raises(LLMServiceError):
            await rag_engine.ask_question(
                question="What is machine learning?",
                tenant_id=test_tenant.id,
                user_id=test_user.id
            )
    
    @pytest.mark.asyncio
    async def test_ask_question_search_error(self, rag_engine, test_user, test_tenant, mock_search_service):
        """Test handling search service errors."""
        mock_search_service.hybrid_search.side_effect = Exception("Search service error")
        
        with pytest.raises(SearchServiceError):
            await rag_engine.ask_question(
                question="What is AI?",
                tenant_id=test_tenant.id,
                user_id=test_user.id
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations(self, rag_engine):
        """Test citation generation from search results."""
        search_results = [
            {
                "document_id": "doc_1",
                "chunk_id": "chunk_1",
                "chunk_text": "This is a test chunk",
                "source_title": "Test Document",
                "source_type": "academic",
                "confidence": 0.95,
                "metadata": {"page": 5}
            }
        ]
        
        citations = rag_engine._generate_citations(search_results)
        
        assert len(citations) == 1
        citation = citations[0]
        
        assert citation["chunk_text"] == "This is a test chunk"
        assert citation["source_title"] == "Test Document"
        assert citation["confidence"] == 0.95
        assert citation["metadata"]["page"] == 5
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_score(self, rag_engine):
        """Test confidence score calculation."""
        citations = [
            {"confidence": 0.95},
            {"confidence": 0.88},
            {"confidence": 0.92}
        ]
        
        confidence = rag_engine._calculate_confidence_score(citations)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # Should be high with good citations
    
    @pytest.mark.asyncio
    async def test_format_context_for_llm(self, rag_engine):
        """Test formatting context for LLM input."""
        search_results = [
            {
                "chunk_text": "AI is a broad field of computer science.",
                "source_title": "AI Introduction",
                "confidence": 0.95
            },
            {
                "chunk_text": "Machine learning is a subset of AI.",
                "source_title": "ML Basics",
                "confidence": 0.88
            }
        ]
        
        context = rag_engine._format_context_for_llm(search_results)
        
        assert "AI is a broad field" in context
        assert "Machine learning is a subset" in context
        assert "Source:" in context
    
    @pytest.mark.asyncio
    async def test_conversation_management(self, rag_engine, test_user, test_tenant, db_session):
        """Test conversation creation and message storage."""
        question = "What is artificial intelligence?"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            mode=RAGMode.CONVERSATIONAL
        )
        
        conversation_id = result["conversation_id"]
        assert conversation_id is not None
        
        # Verify conversation was created in database
        conversation = await db_session.get(Conversation, conversation_id)
        assert conversation is not None
        assert conversation.user_id == test_user.id
        assert conversation.tenant_id == test_tenant.id
    
    @pytest.mark.asyncio
    async def test_context_compression(self, rag_engine):
        """Test context compression for long documents."""
        # Create long search results
        long_results = []
        for i in range(20):
            long_results.append({
                "chunk_text": f"This is chunk {i} with some content about AI and ML." * 50,
                "source_title": f"Document {i}",
                "confidence": 0.8
            })
        
        compressed_context = rag_engine._compress_context(long_results, max_tokens=1000)
        
        # Should be compressed to fit within token limit
        assert len(compressed_context) < len(str(long_results))
        assert "AI and ML" in compressed_context
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self, rag_engine, test_user, test_tenant):
        """Test multilingual question handling."""
        hebrew_question = "מה זה בינה מלאכותית?"
        
        result = await rag_engine.ask_question(
            question=hebrew_question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            language="he"
        )
        
        assert "answer" in result
        assert "language" in result
        assert result["language"] == "he"
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, rag_engine, test_user, test_tenant):
        """Test streaming response functionality."""
        question = "Explain machine learning in detail"
        
        stream = rag_engine.ask_question_stream(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id
        )
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
            assert "type" in chunk
            assert chunk["type"] in ["citation", "answer_chunk", "final_result"]
        
        assert len(chunks) > 0
        assert any(chunk["type"] == "final_result" for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_rag_caching(self, rag_engine, test_user, test_tenant, redis_client):
        """Test RAG response caching."""
        question = "What is machine learning?"
        
        # First request
        result1 = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            use_cache=True
        )
        
        # Second identical request should use cache
        result2 = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            use_cache=True
        )
        
        assert result1["answer"] == result2["answer"]
        assert result2.get("from_cache") is True
    
    @pytest.mark.asyncio
    async def test_personalized_rag(self, rag_engine, test_user, test_tenant, mock_personalization):
        """Test personalized RAG responses."""
        question = "What is AI?"
        
        await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            personalize=True
        )
        
        # Verify personalization was applied
        mock_personalization.personalize_search_results.assert_called_once()
        mock_personalization.get_user_preferences.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_analytics(self, rag_engine, test_user, test_tenant, redis_client):
        """Test RAG analytics tracking."""
        question = "What is deep learning?"
        
        result = await rag_engine.ask_question(
            question=question,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            track_analytics=True
        )
        
        # Verify analytics were recorded
        analytics_key = f"rag_analytics:{test_tenant.id}:{datetime.now().strftime('%Y-%m-%d')}"
        analytics_data = await redis_client.get(analytics_key)
        
        assert analytics_data is not None
        assert "questions_asked" in analytics_data or result.get("analytics_tracked") is True