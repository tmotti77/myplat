"""Document management and processing endpoints."""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, func
from pydantic import BaseModel, Field
import asyncio
from io import BytesIO

from ..core.database import get_db
from ..core.auth import get_current_active_user
from ..models.user import User
from ..models.document import Document, DocumentStatus
from ..models.tenant import Tenant
from ..services.document_processor import DocumentProcessor
from ..services.embedding_service import EmbeddingService
from ..services.storage_service import StorageService
from ..middleware.dependencies import get_document_processor, get_embedding_service, get_storage_service

router = APIRouter()


class DocumentUploadRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    language: str = "en"
    processing_options: Dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    file_size: int
    file_type: str
    status: DocumentStatus
    upload_date: datetime
    last_updated: datetime
    processed_chunks: int
    total_chunks: int
    language: str
    category: Optional[str]
    tags: List[str]
    description: Optional[str]
    metadata: Dict[str, Any]
    tenant_id: str
    user_id: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ChunkResponse(BaseModel):
    id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding_id: Optional[str]


@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    language: str = Form("en"),
    processing_options: Optional[str] = Form("{}"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
    document_processor: DocumentProcessor = Depends(get_document_processor)
):
    """Upload and process a document."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file size (from settings)
        content = await file.read()
        if len(content) > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 100MB."
            )
        
        # Check file type
        allowed_types = {
            ".pdf", ".txt", ".docx", ".doc", ".md", ".html", ".htm",
            ".json", ".csv", ".xlsx", ".xls", ".pptx", ".ppt"
        }
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Parse processing options
        import json
        try:
            proc_options = json.loads(processing_options) if processing_options else {}
        except json.JSONDecodeError:
            proc_options = {}
        
        # Generate document ID and file path
        document_id = str(uuid.uuid4())
        file_path = f"documents/{current_user.tenant_id}/{document_id}/{file.filename}"
        
        # Store file
        storage_url = await storage_service.store_file(
            file_path=file_path,
            content=content,
            content_type=file.content_type
        )
        
        # Create document record
        document = Document(
            id=document_id,
            title=title or Path(file.filename).stem,
            filename=file.filename,
            file_path=file_path,
            storage_url=storage_url,
            file_size=len(content),
            file_type=file.content_type,
            status=DocumentStatus.UPLOADING,
            language=language,
            category=category,
            tags=tag_list,
            description=description,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            processing_options=proc_options
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Start background processing
        asyncio.create_task(
            document_processor.process_document_async(document_id)
        )
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document_id,
            "status": "processing",
            "estimated_processing_time": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[DocumentStatus] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("upload_date", regex="^(upload_date|title|file_size|last_updated)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's documents with filtering and pagination."""
    try:
        # Build query
        query = select(Document).where(
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        # Apply filters
        if status_filter:
            query = query.where(Document.status == status_filter)
        
        if category:
            query = query.where(Document.category == category)
        
        if search:
            query = query.where(
                Document.title.ilike(f"%{search}%") |
                Document.description.ilike(f"%{search}%") |
                Document.filename.ilike(f"%{search}%")
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar()
        
        # Apply sorting
        sort_column = getattr(Document, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        
        return DocumentListResponse(
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document details."""
    try:
        # Get document
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse.model_validate(document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update document metadata."""
    try:
        # Get document
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Update allowed fields
        allowed_fields = {"title", "description", "tags", "category"}
        
        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(document, field, value)
        
        document.last_updated = datetime.utcnow()
        
        await db.commit()
        await db.refresh(document)
        
        return DocumentResponse.model_validate(document)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Delete document and all associated data."""
    try:
        # Get document
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete from storage
        if document.file_path:
            await storage_service.delete_file(document.file_path)
        
        # Delete from database (cascades to chunks, embeddings, etc.)
        await db.delete(document)
        await db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Download original document file."""
    try:
        # Get document
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get file content
        file_content = await storage_service.get_file(document.file_path)
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage"
            )
        
        # Return file as streaming response
        def iterfile():
            yield file_content
        
        return StreamingResponse(
            iterfile(),
            media_type=document.file_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{document.filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}"
        )


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document chunks."""
    try:
        # Verify document access
        doc_query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        doc_result = await db.execute(doc_query)
        document = doc_result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get chunks
        from ..models.chunk import Chunk
        chunks_query = select(Chunk).where(
            Chunk.document_id == document_id
        ).order_by(Chunk.chunk_index)
        
        chunks_result = await db.execute(chunks_query)
        chunks = chunks_result.scalars().all()
        
        return [
            ChunkResponse(
                id=chunk.id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                metadata=chunk.extra_metadata or {},
                embedding_id=chunk.embedding_id
            )
            for chunk in chunks
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document chunks: {str(e)}"
        )


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    processing_options: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    document_processor: DocumentProcessor = Depends(get_document_processor)
):
    """Reprocess document with new options."""
    try:
        # Get document
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if document can be reprocessed
        if document.status == DocumentStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is already being processed"
            )
        
        # Update processing options if provided
        if processing_options:
            document.processing_options = processing_options
        
        # Reset processing status
        document.status = DocumentStatus.PROCESSING
        document.processed_chunks = 0
        document.last_updated = datetime.utcnow()
        
        await db.commit()
        
        # Start reprocessing
        asyncio.create_task(
            document_processor.process_document_async(document_id)
        )
        
        return {
            "message": "Document reprocessing started",
            "document_id": document_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess document: {str(e)}"
        )


@router.get("/{document_id}/status")
async def get_processing_status(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document processing status."""
    try:
        # Get document
        query = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
            Document.user_id == current_user.id
        )
        
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Calculate progress
        progress = 0
        if document.total_chunks > 0:
            progress = (document.processed_chunks / document.total_chunks) * 100
        
        return {
            "document_id": document_id,
            "status": document.status.value,
            "processed_chunks": document.processed_chunks,
            "total_chunks": document.total_chunks,
            "progress_percentage": round(progress, 2),
            "last_updated": document.last_updated,
            "error_message": document.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )