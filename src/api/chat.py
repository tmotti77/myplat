"""Chat and conversation management endpoints."""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, func, desc
from pydantic import BaseModel, Field
import json
import asyncio

from ..core.database import get_db
from ..core.auth import get_current_active_user
from ..models.user import User
from ..models.conversation import Conversation, ConversationStatus
from ..models.message import Message, MessageRole, MessageType
from ..services.chat_service import ChatService
from ..services.rag_service import RAGService
from ..middleware.dependencies import get_chat_service, get_rag_service
from ..core.config import settings

router = APIRouter()


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = MessageType.TEXT
    context: Optional[Dict[str, Any]] = None
    search_params: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    message_type: MessageType
    timestamp: datetime
    context: Optional[Dict[str, Any]]
    sources: Optional[List[Dict[str, Any]]]
    token_usage: Optional[Dict[str, int]]
    processing_time_ms: Optional[int]

    class Config:
        from_attributes = True


class ConversationRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_at: Optional[datetime]
    context: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ConversationWithMessagesResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    stream: bool = False
    model: Optional[str] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=4000)
    include_sources: bool = True
    search_params: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    token_usage: Dict[str, int]
    processing_time_ms: int
    model_used: str


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation."""
    try:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            title=conversation_data.title or "New Conversation",
            description=conversation_data.description,
            status=ConversationStatus.ACTIVE,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            context=conversation_data.context or {}
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return ConversationResponse.model_validate(conversation)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ConversationStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations."""
    try:
        query = select(Conversation).where(
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        if status_filter:
            query = query.where(Conversation.status == status_filter)
        
        # Order by last activity
        query = query.order_by(desc(Conversation.updated_at))
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        return [ConversationResponse.model_validate(conv) for conv in conversations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation details with messages."""
    try:
        # Get conversation
        conv_query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages if requested
        messages = []
        if include_messages:
            msg_query = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp)
            
            msg_result = await db.execute(msg_query)
            messages = [MessageResponse.model_validate(msg) for msg in msg_result.scalars().all()]
        
        return ConversationWithMessagesResponse(
            conversation=ConversationResponse.model_validate(conversation),
            messages=messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation metadata."""
    try:
        # Get conversation
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Update allowed fields
        allowed_fields = {"title", "description", "context", "status"}
        
        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(conversation, field, value)
        
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(conversation)
        
        return ConversationResponse.model_validate(conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation and all messages."""
    try:
        # Get conversation
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete conversation (messages will be deleted via cascade)
        await db.delete(conversation)
        await db.commit()
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    message_data: MessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a conversation."""
    try:
        # Verify conversation access
        conv_query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message_data.content,
            message_type=message_data.message_type,
            context=message_data.context,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
        
        db.add(message)
        
        # Update conversation
        conversation.updated_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()
        conversation.message_count = conversation.message_count + 1
        
        await db.commit()
        await db.refresh(message)
        
        return MessageResponse.model_validate(message)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message and get AI response."""
    start_time = datetime.now()
    
    try:
        # Get or create conversation
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            # Create new conversation
            conversation = Conversation(
                id=str(uuid.uuid4()),
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
                status=ConversationStatus.ACTIVE,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id
            )
            db.add(conversation)
            await db.commit()
            conversation_id = conversation.id
        else:
            # Verify conversation access
            conv_query = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == current_user.tenant_id,
                Conversation.user_id == current_user.id
            )
            conv_result = await db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()
            
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        # Create user message
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=chat_request.message,
            message_type=MessageType.TEXT,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
        db.add(user_message)
        
        # Get chat response
        chat_response = await chat_service.generate_response(
            message=chat_request.message,
            conversation_id=conversation_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            model=chat_request.model or settings.DEFAULT_LLM_MODEL,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            include_sources=chat_request.include_sources,
            search_params=chat_request.search_params
        )
        
        # Create assistant message
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=chat_response.content,
            message_type=MessageType.TEXT,
            sources=chat_response.sources,
            token_usage=chat_response.token_usage,
            processing_time_ms=chat_response.processing_time_ms,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id
        )
        db.add(assistant_message)
        
        # Update conversation
        conversation = await db.get(Conversation, conversation_id)
        conversation.updated_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()
        conversation.message_count = conversation.message_count + 2
        
        await db.commit()
        
        # Calculate total processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_message.id,
            content=chat_response.content,
            sources=chat_response.sources or [],
            token_usage=chat_response.token_usage,
            processing_time_ms=processing_time,
            model_used=chat_response.model_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Stream chat response."""
    async def generate_stream():
        try:
            # Similar setup as regular chat but with streaming
            conversation_id = chat_request.conversation_id
            if not conversation_id:
                # Create new conversation
                conversation = Conversation(
                    id=str(uuid.uuid4()),
                    title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
                    status=ConversationStatus.ACTIVE,
                    tenant_id=current_user.tenant_id,
                    user_id=current_user.id
                )
                db.add(conversation)
                await db.commit()
                conversation_id = conversation.id
            
            # Create user message
            user_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=chat_request.message,
                message_type=MessageType.TEXT,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id
            )
            db.add(user_message)
            await db.commit()
            
            # Stream response
            full_content = ""
            async for chunk in chat_service.generate_response_stream(
                message=chat_request.message,
                conversation_id=conversation_id,
                user_id=current_user.id,
                tenant_id=current_user.tenant_id,
                model=chat_request.model or settings.DEFAULT_LLM_MODEL,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
                include_sources=chat_request.include_sources,
                search_params=chat_request.search_params
            ):
                full_content += chunk.get('content', '')
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # Save final assistant message
            assistant_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=full_content,
                message_type=MessageType.TEXT,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id
            )
            db.add(assistant_message)
            
            # Update conversation
            conversation = await db.get(Conversation, conversation_id)
            conversation.updated_at = datetime.utcnow()
            conversation.last_message_at = datetime.utcnow()
            conversation.message_count = conversation.message_count + 2
            
            await db.commit()
            
            # Send final completion message
            yield f"data: {json.dumps({'type': 'complete', 'conversation_id': conversation_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a conversation."""
    try:
        # Verify conversation access
        conv_query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp)
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return [MessageResponse.model_validate(msg) for msg in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/stats")
async def get_chat_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat statistics."""
    try:
        # Conversation stats
        conv_stats_query = select([
            func.count(Conversation.id).label('total_conversations'),
            func.count().filter(Conversation.status == ConversationStatus.ACTIVE).label('active_conversations'),
            func.sum(Conversation.message_count).label('total_messages')
        ]).where(
            Conversation.tenant_id == current_user.tenant_id,
            Conversation.user_id == current_user.id
        )
        
        conv_stats_result = await db.execute(conv_stats_query)
        conv_stats = conv_stats_result.fetchone()
        
        # Message stats
        msg_stats_query = select([
            func.count(Message.id).label('total_messages'),
            func.count().filter(Message.role == MessageRole.USER).label('user_messages'),
            func.count().filter(Message.role == MessageRole.ASSISTANT).label('assistant_messages'),
            func.sum(Message.token_usage['total_tokens']).label('total_tokens')
        ]).where(
            Message.tenant_id == current_user.tenant_id,
            Message.user_id == current_user.id
        )
        
        msg_stats_result = await db.execute(msg_stats_query)
        msg_stats = msg_stats_result.fetchone()
        
        return {
            "conversations": {
                "total": conv_stats.total_conversations or 0,
                "active": conv_stats.active_conversations or 0,
                "avg_messages_per_conversation": (
                    round(conv_stats.total_messages / conv_stats.total_conversations, 1)
                    if conv_stats.total_conversations > 0 else 0
                )
            },
            "messages": {
                "total": msg_stats.total_messages or 0,
                "user_messages": msg_stats.user_messages or 0,
                "assistant_messages": msg_stats.assistant_messages or 0
            },
            "usage": {
                "total_tokens": msg_stats.total_tokens or 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat stats: {str(e)}"
        )