"""Complete RAG engine with citations, confidence scoring, and structured output."""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

from src.core.config import settings
from src.core.database import get_db_session
from src.core.logging import get_logger, LoggerMixin, LoggedOperation, log_performance
from src.models.conversation import Conversation, ConversationStatus
from src.models.message import Message, MessageType, MessageRole
from src.models.rag_event import RAGEvent, RAGMethod
from src.models.citation import Citation
from src.services.cache import cache_service
from src.services.search import search_service
from src.services.llm_router import llm_router_service
from src.services.embedding import embedding_service

logger = get_logger(__name__)


class RAGMode(str, Enum):
    """RAG operation modes."""
    STANDARD = "standard"          # Normal Q&A
    CONVERSATIONAL = "conversational"  # Multi-turn conversation
    RESEARCH = "research"          # Deep research mode
    SUMMARIZATION = "summarization"  # Document summarization
    COMPARISON = "comparison"      # Compare sources
    FACT_CHECK = "fact_check"     # Fact checking mode


class ConfidenceLevel(str, Enum):
    """Confidence levels for RAG responses."""
    VERY_HIGH = "very_high"      # 90-100%
    HIGH = "high"                # 80-90%
    MEDIUM = "medium"            # 60-80%
    LOW = "low"                  # 40-60%
    VERY_LOW = "very_low"        # 0-40%


class RAGEngine(LoggerMixin):
    """Complete RAG engine for question answering with citations and confidence scoring."""
    
    def __init__(self):
        self._confidence_thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.9,
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.4,
            ConfidenceLevel.VERY_LOW: 0.0,
        }
        self._system_prompts = {}
        
    async def initialize(self):
        """Initialize RAG engine."""
        try:
            # Load system prompts
            await self._load_system_prompts()
            
            self.log_info("RAG engine initialized")
            
        except Exception as e:
            self.log_error("Failed to initialize RAG engine", error=e)
            raise
    
    async def cleanup(self):
        """Clean up RAG engine."""
        try:
            self.log_info("RAG engine cleaned up")
        except Exception as e:
            self.log_error("Error during RAG cleanup", error=e)
    
    async def ask_question(
        self,
        question: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        mode: RAGMode = RAGMode.STANDARD,
        context: Optional[Dict[str, Any]] = None,
        sources: Optional[List[str]] = None,
        language: str = "en",
        model_preference: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        include_citations: bool = True,
        include_confidence: bool = True,
        streaming: bool = False
    ) -> Dict[str, Any]:
        """Ask a question and get RAG-powered answer with citations and confidence."""
        
        start_time = time.time()
        rag_event_id = str(uuid.uuid4())
        
        with LoggedOperation("rag_question", rag_event_id=rag_event_id, question=question[:100]):
            try:
                # Create or get conversation
                if conversation_id:
                    conversation = await self._get_conversation(conversation_id, tenant_id)
                    if not conversation:
                        raise ValueError(f"Conversation {conversation_id} not found")
                else:
                    conversation = await self._create_conversation(
                        tenant_id=tenant_id,
                        user_id=user_id,
                        mode=mode.value,
                        language=language
                    )
                    conversation_id = str(conversation.id)
                
                # Store user message
                user_message = await self._store_message(
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=question,
                    metadata=context or {}
                )
                
                # Retrieve relevant context
                retrieval_result = await self._retrieve_context(
                    question=question,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    conversation=conversation,
                    sources=sources,
                    language=language,
                    mode=mode
                )
                
                # Prepare messages for LLM
                messages = await self._prepare_llm_messages(
                    question=question,
                    conversation=conversation,
                    retrieval_result=retrieval_result,
                    mode=mode,
                    language=language
                )
                
                # Generate response using LLM router
                llm_response = await llm_router_service.route_request(
                    messages=messages,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    model_preference=model_preference,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    context_requirements={
                        "supports_citations": include_citations,
                        "language": language,
                        "requires_reasoning": True
                    }
                )
                
                # Extract and structure response
                structured_response = await self._structure_response(
                    llm_response=llm_response,
                    retrieval_result=retrieval_result,
                    include_citations=include_citations,
                    include_confidence=include_confidence
                )
                
                # Calculate confidence score
                if include_confidence:
                    confidence_score = await self._calculate_confidence(
                        question=question,
                        answer=structured_response["answer"],
                        retrieval_result=retrieval_result,
                        llm_response=llm_response
                    )
                    structured_response["confidence"] = confidence_score
                
                # Store assistant message
                assistant_message = await self._store_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=structured_response["answer"],
                    metadata={
                        "confidence": structured_response.get("confidence", {}),
                        "citations": structured_response.get("citations", []),
                        "model_used": llm_response["model_used"],
                        "cost_usd": llm_response["cost_usd"],
                        "retrieval_method": retrieval_result["method"],
                        "sources_count": len(retrieval_result["sources"])
                    }
                )
                
                # Log RAG event
                duration_ms = (time.time() - start_time) * 1000
                await self._log_rag_event(
                    event_id=rag_event_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    question=question,
                    answer=structured_response["answer"],
                    retrieval_result=retrieval_result,
                    llm_response=llm_response,
                    confidence=structured_response.get("confidence", {}),
                    duration_ms=duration_ms,
                    mode=mode
                )
                
                # Performance logging
                log_performance(
                    "rag_question",
                    duration_ms,
                    question_length=len(question),
                    answer_length=len(structured_response["answer"]),
                    sources_retrieved=len(retrieval_result["sources"]),
                    citations_count=len(structured_response.get("citations", [])),
                    mode=mode.value
                )
                
                return {
                    "conversation_id": conversation_id,
                    "message_id": str(assistant_message.id),
                    "answer": structured_response["answer"],
                    "citations": structured_response.get("citations", []),
                    "confidence": structured_response.get("confidence", {}),
                    "sources": retrieval_result["sources"],
                    "model_used": llm_response["model_used"],
                    "cost_usd": llm_response["cost_usd"],
                    "latency_ms": duration_ms,
                    "retrieval_method": retrieval_result["method"],
                    "language": language,
                    "mode": mode.value
                }
                
            except Exception as e:
                # Log error event
                await self._log_rag_event(
                    event_id=rag_event_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    question=question,
                    answer="",
                    retrieval_result={},
                    llm_response={},
                    confidence={},
                    duration_ms=(time.time() - start_time) * 1000,
                    mode=mode,
                    error=str(e)
                )
                
                self.log_error(
                    "RAG question failed",
                    rag_event_id=rag_event_id,
                    question=question[:100],
                    tenant_id=tenant_id,
                    error=e
                )
                raise
    
    async def _retrieve_context(
        self,
        question: str,
        tenant_id: str,
        user_id: Optional[str],
        conversation: Conversation,
        sources: Optional[List[str]],
        language: str,
        mode: RAGMode
    ) -> Dict[str, Any]:
        """Retrieve relevant context for the question."""
        
        try:
            # Prepare search filters
            filters = {}
            if sources:
                filters["source_ids"] = sources
            
            # Adjust search parameters based on mode
            search_params = self._get_search_parameters(mode)
            
            # Add conversation context for conversational mode
            enhanced_query = question
            if mode == RAGMode.CONVERSATIONAL and conversation:
                enhanced_query = await self._enhance_query_with_conversation(
                    question, conversation
                )
            
            # Perform hybrid search
            search_results = await search_service.hybrid_search(
                query=enhanced_query,
                tenant_id=tenant_id,
                user_id=user_id,
                k=search_params["k"],
                filters=filters,
                rerank=search_params["rerank"],
                use_mmr=search_params["use_mmr"],
                language=language
            )
            
            # Post-process results based on mode
            processed_results = await self._post_process_search_results(
                search_results, mode, question
            )
            
            return {
                "sources": processed_results,
                "method": "hybrid_search",
                "query_enhanced": enhanced_query != question,
                "total_candidates": len(search_results),
                "filtered_count": len(processed_results)
            }
            
        except Exception as e:
            self.log_error("Context retrieval failed", error=e)
            return {
                "sources": [],
                "method": "failed",
                "query_enhanced": False,
                "total_candidates": 0,
                "filtered_count": 0
            }
    
    def _get_search_parameters(self, mode: RAGMode) -> Dict[str, Any]:
        """Get search parameters based on RAG mode."""
        
        parameters = {
            RAGMode.STANDARD: {"k": 10, "rerank": True, "use_mmr": True},
            RAGMode.CONVERSATIONAL: {"k": 8, "rerank": True, "use_mmr": True},
            RAGMode.RESEARCH: {"k": 20, "rerank": True, "use_mmr": True},
            RAGMode.SUMMARIZATION: {"k": 15, "rerank": False, "use_mmr": False},
            RAGMode.COMPARISON: {"k": 12, "rerank": True, "use_mmr": True},
            RAGMode.FACT_CHECK: {"k": 15, "rerank": True, "use_mmr": False},
        }
        
        return parameters.get(mode, parameters[RAGMode.STANDARD])
    
    async def _enhance_query_with_conversation(
        self,
        question: str,
        conversation: Conversation
    ) -> str:
        """Enhance query with conversation context."""
        
        try:
            # Get recent messages from conversation
            async with get_db_session() as session:
                from sqlalchemy import select
                
                query = (
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.desc())
                    .limit(6)  # Last 3 exchanges
                )
                
                result = await session.execute(query)
                messages = result.scalars().all()
            
            if not messages:
                return question
            
            # Build context from recent messages
            context_parts = []
            for message in reversed(messages):
                if message.role == MessageRole.USER.value:
                    context_parts.append(f"Previous question: {message.content}")
                elif message.role == MessageRole.ASSISTANT.value:
                    context_parts.append(f"Previous answer: {message.content[:200]}...")
            
            # Combine context with current question
            if context_parts:
                context = " ".join(context_parts[-4:])  # Last 2 exchanges
                enhanced_query = f"Context: {context}\n\nCurrent question: {question}"
                return enhanced_query
            
            return question
            
        except Exception as e:
            self.log_error("Query enhancement failed", error=e)
            return question
    
    async def _post_process_search_results(
        self,
        results: List[Dict[str, Any]],
        mode: RAGMode,
        question: str
    ) -> List[Dict[str, Any]]:
        """Post-process search results based on mode."""
        
        try:
            if mode == RAGMode.FACT_CHECK:
                # For fact-checking, prioritize authoritative sources
                results = [r for r in results if r.get("quality_score", 0) >= 0.7]
            
            elif mode == RAGMode.RESEARCH:
                # For research, ensure diverse sources
                seen_sources = set()
                diverse_results = []
                for result in results:
                    source_id = result.get("source_id")
                    if source_id not in seen_sources or len(diverse_results) < 5:
                        diverse_results.append(result)
                        seen_sources.add(source_id)
                        if len(diverse_results) >= 15:
                            break
                results = diverse_results
            
            elif mode == RAGMode.COMPARISON:
                # For comparison, group by sources and ensure multiple perspectives
                source_groups = {}
                for result in results:
                    source_id = result.get("source_id")
                    if source_id not in source_groups:
                        source_groups[source_id] = []
                    source_groups[source_id].append(result)
                
                # Take top results from each source
                balanced_results = []
                for source_results in source_groups.values():
                    balanced_results.extend(source_results[:2])
                results = balanced_results[:12]
            
            return results
            
        except Exception as e:
            self.log_error("Search results post-processing failed", error=e)
            return results
    
    async def _prepare_llm_messages(
        self,
        question: str,
        conversation: Conversation,
        retrieval_result: Dict[str, Any],
        mode: RAGMode,
        language: str
    ) -> List[Dict[str, str]]:
        """Prepare messages for LLM including system prompt and context."""
        
        # Get system prompt for mode
        system_prompt = self._system_prompts.get(mode, self._system_prompts[RAGMode.STANDARD])
        
        # Format context from retrieval results
        context = self._format_context_for_llm(retrieval_result["sources"])
        
        # Build conversation history for conversational mode
        conversation_history = ""
        if mode == RAGMode.CONVERSATIONAL and conversation:
            conversation_history = await self._build_conversation_history(conversation)
        
        messages = [
            {
                "role": "system",
                "content": system_prompt.format(
                    language=language,
                    mode=mode.value,
                    context=context,
                    conversation_history=conversation_history
                )
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        return messages
    
    def _format_context_for_llm(self, sources: List[Dict[str, Any]]) -> str:
        """Format search results as context for LLM."""
        
        if not sources:
            return "No relevant context found."
        
        context_parts = []
        for i, source in enumerate(sources, 1):
            text = source.get("text", "")
            document_title = source.get("document_title", "Unknown")
            section = source.get("section", "")
            page_number = source.get("page_number")
            
            # Build source identifier
            source_id = f"[{i}]"
            source_info = f"Document: {document_title}"
            if section:
                source_info += f", Section: {section}"
            if page_number:
                source_info += f", Page: {page_number}"
            
            context_parts.append(f"{source_id} {source_info}\n{text}\n")
        
        return "\n".join(context_parts)
    
    async def _build_conversation_history(self, conversation: Conversation) -> str:
        """Build conversation history for context."""
        
        try:
            async with get_db_session() as session:
                from sqlalchemy import select
                
                query = (
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.asc())
                    .limit(10)  # Last 5 exchanges
                )
                
                result = await session.execute(query)
                messages = result.scalars().all()
            
            if not messages:
                return ""
            
            history_parts = []
            for message in messages[:-1]:  # Exclude current question
                role = "User" if message.role == MessageRole.USER.value else "Assistant"
                content = message.content[:300] + "..." if len(message.content) > 300 else message.content
                history_parts.append(f"{role}: {content}")
            
            return "\n".join(history_parts)
            
        except Exception as e:
            self.log_error("Conversation history building failed", error=e)
            return ""
    
    async def _structure_response(
        self,
        llm_response: Dict[str, Any],
        retrieval_result: Dict[str, Any],
        include_citations: bool,
        include_confidence: bool
    ) -> Dict[str, Any]:
        """Structure the LLM response with citations and metadata."""
        
        try:
            # Extract answer from LLM response
            answer = llm_response["response"]["choices"][0]["message"]["content"]
            
            structured_response = {"answer": answer}
            
            # Extract and create citations if requested
            if include_citations:
                citations = await self._extract_citations(
                    answer=answer,
                    sources=retrieval_result["sources"]
                )
                structured_response["citations"] = citations
            
            return structured_response
            
        except Exception as e:
            self.log_error("Response structuring failed", error=e)
            return {"answer": "I apologize, but I encountered an error while processing your question."}
    
    async def _extract_citations(
        self,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract citations from answer and match with sources."""
        
        try:
            citations = []
            
            # Look for citation markers in the answer [1], [2], etc.
            import re
            citation_pattern = r'\[(\d+)\]'
            matches = re.findall(citation_pattern, answer)
            
            for match in matches:
                source_index = int(match) - 1  # Convert to 0-based index
                
                if 0 <= source_index < len(sources):
                    source = sources[source_index]
                    
                    citation = {
                        "id": str(uuid.uuid4()),
                        "text": source.get("text", "")[:200] + "...",
                        "document_title": source.get("document_title", ""),
                        "document_url": source.get("document_url"),
                        "section": source.get("section"),
                        "page_number": source.get("page_number"),
                        "source_id": source.get("source_id"),
                        "chunk_id": source.get("chunk_id"),
                        "relevance_score": source.get("hybrid_score", 0.0),
                        "citation_number": int(match),
                        "reason": "direct_reference"
                    }
                    
                    citations.append(citation)
            
            # Store citations in database
            if citations:
                await self._store_citations(citations)
            
            return citations
            
        except Exception as e:
            self.log_error("Citation extraction failed", error=e)
            return []
    
    async def _calculate_confidence(
        self,
        question: str,
        answer: str,
        retrieval_result: Dict[str, Any],
        llm_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate confidence score for the RAG response."""
        
        try:
            confidence_factors = {}
            
            # Source quality factor (0-1)
            sources = retrieval_result.get("sources", [])
            if sources:
                avg_quality = sum(s.get("quality_score", 0.5) for s in sources) / len(sources)
                source_quality_factor = min(1.0, avg_quality)
            else:
                source_quality_factor = 0.0
            
            confidence_factors["source_quality"] = source_quality_factor
            
            # Retrieval relevance factor (0-1)
            if sources:
                avg_relevance = sum(s.get("hybrid_score", 0.5) for s in sources[:5]) / min(5, len(sources))
                relevance_factor = min(1.0, avg_relevance)
            else:
                relevance_factor = 0.0
            
            confidence_factors["relevance"] = relevance_factor
            
            # Source coverage factor (0-1)
            unique_sources = len(set(s.get("source_id") for s in sources))
            coverage_factor = min(1.0, unique_sources / 3.0)  # Ideal: 3+ sources
            confidence_factors["coverage"] = coverage_factor
            
            # Answer completeness factor (0-1)
            answer_length = len(answer.split())
            completeness_factor = min(1.0, answer_length / 100.0)  # Ideal: 100+ words
            confidence_factors["completeness"] = completeness_factor
            
            # Model confidence (if available)
            model_confidence = 0.8  # Default for most models
            confidence_factors["model"] = model_confidence
            
            # Citation factor (0-1)
            import re
            citation_count = len(re.findall(r'\[\d+\]', answer))
            citation_factor = min(1.0, citation_count / 3.0)  # Ideal: 3+ citations
            confidence_factors["citations"] = citation_factor
            
            # Calculate overall confidence (weighted average)
            weights = {
                "source_quality": 0.25,
                "relevance": 0.25,
                "coverage": 0.15,
                "completeness": 0.10,
                "model": 0.15,
                "citations": 0.10
            }
            
            overall_score = sum(
                confidence_factors[factor] * weight
                for factor, weight in weights.items()
            )
            
            # Determine confidence level
            confidence_level = self._get_confidence_level(overall_score)
            
            return {
                "score": round(overall_score, 3),
                "level": confidence_level.value,
                "factors": confidence_factors,
                "explanation": self._get_confidence_explanation(overall_score, confidence_factors)
            }
            
        except Exception as e:
            self.log_error("Confidence calculation failed", error=e)
            return {
                "score": 0.5,
                "level": ConfidenceLevel.MEDIUM.value,
                "factors": {},
                "explanation": "Unable to calculate confidence"
            }
    
    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level."""
        
        for level, threshold in sorted(self._confidence_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return level
        
        return ConfidenceLevel.VERY_LOW
    
    def _get_confidence_explanation(
        self,
        score: float,
        factors: Dict[str, float]
    ) -> str:
        """Generate explanation for confidence score."""
        
        explanations = []
        
        if factors.get("source_quality", 0) >= 0.8:
            explanations.append("high-quality sources")
        elif factors.get("source_quality", 0) <= 0.4:
            explanations.append("limited source quality")
        
        if factors.get("relevance", 0) >= 0.8:
            explanations.append("highly relevant content")
        elif factors.get("relevance", 0) <= 0.4:
            explanations.append("low content relevance")
        
        if factors.get("coverage", 0) >= 0.7:
            explanations.append("multiple source coverage")
        elif factors.get("coverage", 0) <= 0.3:
            explanations.append("limited source diversity")
        
        if factors.get("citations", 0) >= 0.7:
            explanations.append("well-cited response")
        elif factors.get("citations", 0) <= 0.3:
            explanations.append("few citations")
        
        if explanations:
            return f"Based on: {', '.join(explanations)}"
        else:
            return "Standard confidence assessment"
    
    async def _create_conversation(
        self,
        tenant_id: str,
        user_id: Optional[str],
        mode: str,
        language: str
    ) -> Conversation:
        """Create a new conversation."""
        
        async with get_db_session() as session:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                title="New Conversation",
                status=ConversationStatus.ACTIVE.value,
                language=language,
                mode=mode,
                metadata={}
            )
            
            session.add(conversation)
            await session.commit()
            
            return conversation
    
    async def _get_conversation(
        self,
        conversation_id: str,
        tenant_id: str
    ) -> Optional[Conversation]:
        """Get existing conversation."""
        
        async with get_db_session() as session:
            conversation = await session.get(Conversation, conversation_id)
            
            if conversation and conversation.tenant_id == tenant_id:
                return conversation
            
            return None
    
    async def _store_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        metadata: Dict[str, Any]
    ) -> Message:
        """Store a message in the conversation."""
        
        async with get_db_session() as session:
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role.value,
                content=content,
                message_type=MessageType.TEXT.value,
                metadata=metadata
            )
            
            session.add(message)
            await session.commit()
            
            return message
    
    async def _store_citations(self, citations: List[Dict[str, Any]]):
        """Store citations in database."""
        
        try:
            async with get_db_session() as session:
                citation_objects = []
                
                for citation_data in citations:
                    citation = Citation(
                        id=citation_data["id"],
                        chunk_text=citation_data["text"],
                        source_title=citation_data["document_title"],
                        source_url=citation_data.get("document_url"),
                        chunk_section=citation_data.get("section"),
                        chunk_page=citation_data.get("page_number"),
                        chunk_id=citation_data["chunk_id"],
                        relevance_score=citation_data["relevance_score"],
                        order_index=citation_data["citation_number"],
                        citation_type=citation_data["reason"]
                    )
                    citation_objects.append(citation)
                
                session.add_all(citation_objects)
                await session.commit()
                
        except Exception as e:
            self.log_error("Citation storage failed", error=e)
    
    async def _log_rag_event(
        self,
        event_id: str,
        conversation_id: Optional[str],
        user_id: Optional[str],
        question: str,
        answer: str,
        retrieval_result: Dict[str, Any],
        llm_response: Dict[str, Any],
        confidence: Dict[str, Any],
        duration_ms: float,
        mode: RAGMode,
        error: Optional[str] = None
    ):
        """Log RAG event for analytics."""
        
        try:
            async with get_db_session() as session:
                rag_event = RAGEvent(
                    id=event_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    method=RAGMethod.HYBRID_RAG.value,
                    question_text=question,
                    answer_text=answer,
                    sources_retrieved=len(retrieval_result.get("sources", [])),
                    response_time_ms=int(duration_ms),
                    model_used=llm_response.get("model_used"),
                    total_cost=llm_response.get("cost_usd", 0.0),
                    confidence_score=confidence.get("score"),
                    quality_score=self._calculate_quality_score(
                        question, answer, retrieval_result, confidence
                    ),
                    feedback_score=None,  # To be updated by user feedback
                    metadata={
                        "mode": mode.value,
                        "retrieval_method": retrieval_result.get("method"),
                        "llm_latency_ms": llm_response.get("latency_ms"),
                        "error": error
                    }
                )
                
                session.add(rag_event)
                await session.commit()
                
        except Exception as e:
            self.log_error("RAG event logging failed", error=e)
    
    def _calculate_quality_score(
        self,
        question: str,
        answer: str,
        retrieval_result: Dict[str, Any],
        confidence: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score for the RAG response."""
        
        try:
            # Combine multiple quality factors
            factors = []
            
            # Confidence score
            if confidence.get("score"):
                factors.append(confidence["score"])
            
            # Source quality
            sources = retrieval_result.get("sources", [])
            if sources:
                avg_quality = sum(s.get("quality_score", 0.5) for s in sources) / len(sources)
                factors.append(avg_quality)
            
            # Answer completeness (basic heuristic)
            answer_words = len(answer.split())
            if answer_words >= 50:
                completeness = min(1.0, answer_words / 200.0)
                factors.append(completeness)
            
            # Calculate average
            if factors:
                return sum(factors) / len(factors)
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    async def _load_system_prompts(self):
        """Load system prompts for different RAG modes."""
        
        self._system_prompts = {
            RAGMode.STANDARD: """You are a helpful AI assistant. Answer the user's question based on the provided context. Use the context to provide accurate, informative responses.

Language: {language}
Mode: {mode}

Context:
{context}

Instructions:
- Use ONLY the information from the provided context
- If information is not in the context, clearly state this
- Include relevant citations using [1], [2], etc. format
- Be concise but comprehensive
- Maintain factual accuracy

{conversation_history}""",

            RAGMode.CONVERSATIONAL: """You are a conversational AI assistant. Continue the conversation naturally while staying grounded in the provided context.

Language: {language}
Mode: {mode}

Context:
{context}

Previous conversation:
{conversation_history}

Instructions:
- Reference previous conversation when relevant
- Use context to provide accurate information
- Maintain conversational flow
- Include citations where appropriate
- Be helpful and engaging""",

            RAGMode.RESEARCH: """You are a research assistant. Provide a comprehensive, well-researched answer based on the provided sources.

Language: {language}
Mode: {mode}

Context:
{context}

Instructions:
- Provide detailed, research-quality response
- Synthesize information from multiple sources
- Include comprehensive citations
- Present different perspectives when available
- Structure your response clearly

{conversation_history}""",

            RAGMode.SUMMARIZATION: """You are a summarization expert. Create a comprehensive summary of the provided content.

Language: {language}
Mode: {mode}

Content to summarize:
{context}

Instructions:
- Create a structured summary
- Capture key points and main themes
- Organize information logically
- Include relevant citations
- Maintain accuracy to source material

{conversation_history}""",

            RAGMode.COMPARISON: """You are an analysis expert. Compare and contrast the information from the provided sources.

Language: {language}
Mode: {mode}

Sources to compare:
{context}

Instructions:
- Identify similarities and differences
- Present balanced comparison
- Cite specific sources for each point
- Highlight any conflicting information
- Provide objective analysis

{conversation_history}""",

            RAGMode.FACT_CHECK: """You are a fact-checking assistant. Verify claims against the provided authoritative sources.

Language: {language}
Mode: {mode}

Reference sources:
{context}

Instructions:
- Verify factual accuracy against sources
- Clearly state what can/cannot be verified
- Provide specific citations for verification
- Note any contradictions or uncertainties
- Be precise about confidence levels

{conversation_history}"""
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check RAG engine health."""
        
        health = {
            "status": "healthy",
            "system_prompts_loaded": len(self._system_prompts),
            "search_service_available": False,
            "llm_router_available": False,
            "embedding_service_available": False,
        }
        
        try:
            # Check search service
            search_health = await search_service.health_check()
            health["search_service_available"] = search_health.get("status") == "healthy"
            
            # Check LLM router
            llm_health = await llm_router_service.health_check()
            health["llm_router_available"] = llm_health.get("status") == "healthy"
            
            # Check embedding service
            embedding_health = await embedding_service.health_check()
            health["embedding_service_available"] = embedding_health.get("status") == "healthy"
            
            # Overall status
            if not all([
                health["search_service_available"],
                health["llm_router_available"],
                health["embedding_service_available"]
            ]):
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


# Global RAG engine instance
rag_engine = RAGEngine()