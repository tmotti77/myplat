"""
Integration tests for document workflow
Tests end-to-end document processing from upload to search and RAG
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import io
import os
from datetime import datetime
import uuid
import json

from src.models.document import Document, DocumentStatus, DocumentType
from src.models.collection import Collection
from src.services.ingestion_service import IngestionService
from src.services.embedding_service import EmbeddingService
from src.services.search_service import SearchService
from src.services.rag_engine import RAGEngine

@pytest.mark.integration
@pytest.mark.database
class TestDocumentWorkflow:
    """Test suite for complete document processing workflow."""
    
    @pytest_asyncio.fixture
    async def sample_pdf_content(self):
        """Create sample PDF content for testing."""
        # This would normally be actual PDF bytes
        return b"Mock PDF content for testing document processing workflow"
    
    @pytest_asyncio.fixture
    async def sample_text_content(self):
        """Create sample text content for testing."""
        return "This is a sample document about artificial intelligence and machine learning. " \
               "It covers various topics including neural networks, deep learning, and natural language processing. " \
               "The document provides comprehensive coverage of modern AI techniques and applications."
    
    @pytest.mark.asyncio
    async def test_complete_document_upload_workflow(
        self, 
        async_client: AsyncClient,
        test_user,
        test_collection,
        authenticated_headers,
        sample_pdf_content
    ):
        """Test complete document upload and processing workflow."""
        
        # Mock external services
        with patch('src.services.ingestion_service.IngestionService.process_document') as mock_process, \
             patch('src.services.embedding_service.EmbeddingService.generate_embeddings') as mock_embed:
            
            mock_process.return_value = {
                "success": True,
                "extracted_text": "Sample extracted text from PDF",
                "metadata": {
                    "page_count": 5,
                    "language": "en",
                    "confidence_score": 0.95
                },
                "summary": "Document about AI and ML",
                "keywords": ["AI", "machine learning", "neural networks"]
            }
            
            mock_embed.return_value = [0.1] * 1536  # Mock OpenAI embedding
            
            # Step 1: Upload document
            upload_data = {
                "title": "Test AI Document",
                "collection_id": test_collection.id,
                "auto_process": True
            }
            
            files = {
                "file": ("test_document.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
            }
            
            response = await async_client.post(
                "/api/v1/documents/upload",
                data=upload_data,
                files=files,
                headers=authenticated_headers
            )
            
            assert response.status_code == 201
            upload_result = response.json()
            
            assert "document_id" in upload_result
            assert upload_result["title"] == "Test AI Document"
            assert upload_result["status"] == "uploaded"
            
            document_id = upload_result["document_id"]
            
            # Step 2: Wait for processing (simulate async processing)
            # In real scenario, this would be handled by background workers
            
            # Step 3: Check document status
            response = await async_client.get(
                f"/api/v1/documents/{document_id}",
                headers=authenticated_headers
            )
            
            assert response.status_code == 200
            document_data = response.json()
            
            # Document should be processed successfully
            assert document_data["id"] == document_id
            assert document_data["status"] == "processed"
            assert document_data["processing_metadata"]["confidence_score"] == 0.95
            
            # Step 4: Verify document is searchable
            search_response = await async_client.post(
                "/api/v1/search/hybrid",
                json={
                    "query": "artificial intelligence",
                    "limit": 10,
                    "include_documents": True
                },
                headers=authenticated_headers
            )
            
            assert search_response.status_code == 200
            search_results = search_response.json()
            
            # Our document should appear in search results
            document_found = any(
                result["document_id"] == document_id 
                for result in search_results["results"]
            )
            assert document_found
            
            # Step 5: Test RAG query using the document
            rag_response = await async_client.post(
                "/api/v1/rag/query",
                json={
                    "question": "What does this document say about machine learning?",
                    "document_ids": [document_id],
                    "mode": "standard"
                },
                headers=authenticated_headers
            )
            
            assert rag_response.status_code == 200
            rag_result = rag_response.json()
            
            assert "answer" in rag_result
            assert "citations" in rag_result
            assert len(rag_result["citations"]) > 0
            
            # Citations should reference our document
            citation_found = any(
                citation["document_id"] == document_id
                for citation in rag_result["citations"]
            )
            assert citation_found
    
    @pytest.mark.asyncio
    async def test_document_processing_failure_handling(
        self,
        async_client: AsyncClient,
        test_user,
        test_collection,
        authenticated_headers,
        sample_pdf_content
    ):
        """Test handling of document processing failures."""
        
        # Mock processing failure
        with patch('src.services.ingestion_service.IngestionService.process_document') as mock_process:
            mock_process.side_effect = Exception("OCR processing failed")
            
            upload_data = {
                "title": "Failed Document",
                "collection_id": test_collection.id,
                "auto_process": True
            }
            
            files = {
                "file": ("failed_doc.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
            }
            
            response = await async_client.post(
                "/api/v1/documents/upload",
                data=upload_data,
                files=files,
                headers=authenticated_headers
            )
            
            assert response.status_code == 201
            document_id = response.json()["document_id"]
            
            # Check that document status shows failure
            # Note: In real implementation, this would be updated by background worker
            status_response = await async_client.get(
                f"/api/v1/documents/{document_id}/status",
                headers=authenticated_headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            # Should eventually show failed status
            assert status_data["status"] in ["processing", "failed"]
            
            if status_data["status"] == "failed":
                assert "error_message" in status_data
                assert "retry_count" in status_data
    
    @pytest.mark.asyncio
    async def test_document_update_workflow(
        self,
        async_client: AsyncClient,
        test_document,
        authenticated_headers
    ):
        """Test document update and reprocessing workflow."""
        
        # Step 1: Update document metadata
        update_data = {
            "title": "Updated Document Title",
            "summary": "Updated summary with new information",
            "keywords": ["updated", "keywords", "AI"]
        }
        
        response = await async_client.put(
            f"/api/v1/documents/{test_document.id}",
            json=update_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        updated_doc = response.json()
        
        assert updated_doc["title"] == "Updated Document Title"
        assert updated_doc["summary"] == "Updated summary with new information"
        assert "updated" in updated_doc["keywords"]
        
        # Step 2: Trigger reprocessing
        reprocess_response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/reprocess",
            headers=authenticated_headers
        )
        
        assert reprocess_response.status_code == 202
        reprocess_result = reprocess_response.json()
        
        assert reprocess_result["status"] == "reprocessing_queued"
        assert "job_id" in reprocess_result
    
    @pytest.mark.asyncio
    async def test_bulk_document_operations(
        self,
        async_client: AsyncClient,
        test_user,
        test_collection,
        authenticated_headers,
        db_session
    ):
        """Test bulk document operations."""
        
        # Create multiple test documents
        document_ids = []
        for i in range(3):
            doc = Document(
                id=str(uuid.uuid4()),
                title=f"Bulk Test Document {i+1}",
                filename=f"bulk_doc_{i+1}.pdf",
                file_path=f"/test/bulk_doc_{i+1}.pdf",
                file_size=1024,
                file_type=DocumentType.PDF,
                tenant_id=test_user.tenant_id,
                uploaded_by=test_user.id,
                collection_id=test_collection.id,
                status=DocumentStatus.PROCESSED,
                content=f"Content for bulk document {i+1}",
                created_at=datetime.utcnow()
            )
            db_session.add(doc)
            document_ids.append(doc.id)
        
        await db_session.commit()
        
        # Step 1: Bulk update tags
        bulk_update_data = {
            "document_ids": document_ids,
            "operation": "add_tags",
            "tags": ["bulk_processed", "test_collection"]
        }
        
        response = await async_client.post(
            "/api/v1/documents/bulk/update",
            json=bulk_update_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        bulk_result = response.json()
        
        assert bulk_result["success_count"] == 3
        assert bulk_result["failed_count"] == 0
        
        # Step 2: Bulk move to different collection
        new_collection = Collection(
            id=str(uuid.uuid4()),
            name="New Bulk Collection",
            tenant_id=test_user.tenant_id,
            owner_id=test_user.id,
            created_at=datetime.utcnow()
        )
        db_session.add(new_collection)
        await db_session.commit()
        
        bulk_move_data = {
            "document_ids": document_ids,
            "operation": "move_to_collection",
            "target_collection_id": new_collection.id
        }
        
        move_response = await async_client.post(
            "/api/v1/documents/bulk/update",
            json=bulk_move_data,
            headers=authenticated_headers
        )
        
        assert move_response.status_code == 200
        move_result = move_response.json()
        
        assert move_result["success_count"] == 3
        
        # Verify documents were moved
        for doc_id in document_ids:
            doc_response = await async_client.get(
                f"/api/v1/documents/{doc_id}",
                headers=authenticated_headers
            )
            doc_data = doc_response.json()
            assert doc_data["collection_id"] == new_collection.id
    
    @pytest.mark.asyncio
    async def test_document_versioning_workflow(
        self,
        async_client: AsyncClient,
        test_document,
        authenticated_headers,
        sample_pdf_content
    ):
        """Test document versioning workflow."""
        
        # Step 1: Create new version by uploading new file
        version_data = {
            "create_version": True,
            "version_notes": "Updated with new information"
        }
        
        files = {
            "file": ("updated_document.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
        }
        
        response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/versions",
            data=version_data,
            files=files,
            headers=authenticated_headers
        )
        
        assert response.status_code == 201
        version_result = response.json()
        
        assert "version_id" in version_result
        assert version_result["version_number"] == 2
        assert version_result["notes"] == "Updated with new information"
        
        # Step 2: List document versions
        versions_response = await async_client.get(
            f"/api/v1/documents/{test_document.id}/versions",
            headers=authenticated_headers
        )
        
        assert versions_response.status_code == 200
        versions_data = versions_response.json()
        
        assert len(versions_data["versions"]) == 2
        assert versions_data["current_version"] == 2
        
        # Step 3: Revert to previous version
        revert_response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/versions/1/restore",
            headers=authenticated_headers
        )
        
        assert revert_response.status_code == 200
        revert_result = revert_response.json()
        
        assert revert_result["reverted_to_version"] == 1
        assert revert_result["new_current_version"] == 3  # Creates new version
    
    @pytest.mark.asyncio
    async def test_document_sharing_workflow(
        self,
        async_client: AsyncClient,
        test_document,
        test_admin_user,
        authenticated_headers,
        admin_headers,
        db_session
    ):
        """Test document sharing and collaboration workflow."""
        
        # Step 1: Share document with another user
        share_data = {
            "user_id": test_admin_user.id,
            "permission_level": "read",
            "expires_at": None,
            "notify_user": True
        }
        
        response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/share",
            json=share_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        share_result = response.json()
        
        assert "share_id" in share_result
        assert share_result["permission_level"] == "read"
        
        # Step 2: Verify shared user can access document
        access_response = await async_client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=admin_headers
        )
        
        assert access_response.status_code == 200
        doc_data = access_response.json()
        assert doc_data["id"] == test_document.id
        
        # Step 3: Try to modify document with read-only permission (should fail)
        update_response = await async_client.put(
            f"/api/v1/documents/{test_document.id}",
            json={"title": "Modified by shared user"},
            headers=admin_headers
        )
        
        assert update_response.status_code == 403  # Forbidden
        
        # Step 4: Upgrade permission to write
        permission_update = {
            "permission_level": "write"
        }
        
        permission_response = await async_client.put(
            f"/api/v1/documents/{test_document.id}/share/{test_admin_user.id}",
            json=permission_update,
            headers=authenticated_headers
        )
        
        assert permission_response.status_code == 200
        
        # Step 5: Now modification should work
        update_response = await async_client.put(
            f"/api/v1/documents/{test_document.id}",
            json={"title": "Modified by shared user"},
            headers=admin_headers
        )
        
        assert update_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_document_analytics_workflow(
        self,
        async_client: AsyncClient,
        test_document,
        authenticated_headers
    ):
        """Test document analytics and usage tracking."""
        
        # Step 1: Record document views
        for _ in range(5):
            view_response = await async_client.post(
                f"/api/v1/documents/{test_document.id}/view",
                headers=authenticated_headers
            )
            assert view_response.status_code == 200
        
        # Step 2: Record search interactions
        search_response = await async_client.post(
            "/api/v1/search/hybrid",
            json={
                "query": "test content",
                "track_interaction": True
            },
            headers=authenticated_headers
        )
        assert search_response.status_code == 200
        
        # Step 3: Record RAG interactions
        rag_response = await async_client.post(
            "/api/v1/rag/query",
            json={
                "question": "What is this document about?",
                "document_ids": [test_document.id],
                "track_interaction": True
            },
            headers=authenticated_headers
        )
        assert rag_response.status_code == 200
        
        # Step 4: Get document analytics
        analytics_response = await async_client.get(
            f"/api/v1/documents/{test_document.id}/analytics",
            headers=authenticated_headers
        )
        
        assert analytics_response.status_code == 200
        analytics_data = analytics_response.json()
        
        assert analytics_data["view_count"] >= 5
        assert analytics_data["search_count"] >= 1
        assert analytics_data["rag_count"] >= 1
        assert "daily_stats" in analytics_data
        assert "popular_queries" in analytics_data
    
    @pytest.mark.asyncio
    async def test_document_export_workflow(
        self,
        async_client: AsyncClient,
        test_document,
        authenticated_headers
    ):
        """Test document export functionality."""
        
        # Step 1: Export single document
        export_response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/export",
            json={
                "format": "pdf",
                "include_metadata": True,
                "include_annotations": True
            },
            headers=authenticated_headers
        )
        
        assert export_response.status_code == 200
        
        # Should return file download or export job ID
        if export_response.headers.get("content-type") == "application/pdf":
            # Direct download
            assert len(export_response.content) > 0
        else:
            # Async export job
            export_result = export_response.json()
            assert "export_job_id" in export_result
            
            # Check export status
            job_id = export_result["export_job_id"]
            status_response = await async_client.get(
                f"/api/v1/exports/{job_id}/status",
                headers=authenticated_headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] in ["pending", "processing", "completed"]
    
    @pytest.mark.asyncio
    async def test_document_compliance_workflow(
        self,
        async_client: AsyncClient,
        test_document,
        authenticated_headers
    ):
        """Test document compliance and data protection features."""
        
        # Step 1: Check for PII in document
        pii_response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/scan-pii",
            headers=authenticated_headers
        )
        
        assert pii_response.status_code == 200
        pii_result = pii_response.json()
        
        assert "pii_detected" in pii_result
        assert "detected_entities" in pii_result
        assert "confidence_scores" in pii_result
        
        # Step 2: Apply data retention policy
        retention_response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/retention",
            json={
                "policy": "standard",
                "retention_period_days": 365,
                "auto_delete": False
            },
            headers=authenticated_headers
        )
        
        assert retention_response.status_code == 200
        
        # Step 3: Create audit log entry
        audit_response = await async_client.post(
            f"/api/v1/documents/{test_document.id}/audit",
            json={
                "action": "compliance_review",
                "details": "Document reviewed for compliance requirements"
            },
            headers=authenticated_headers
        )
        
        assert audit_response.status_code == 200
        
        # Step 4: Generate compliance report
        report_response = await async_client.get(
            f"/api/v1/documents/{test_document.id}/compliance-report",
            headers=authenticated_headers
        )
        
        assert report_response.status_code == 200
        report_data = report_response.json()
        
        assert "compliance_status" in report_data
        assert "last_reviewed" in report_data
        assert "retention_policy" in report_data
        assert "audit_trail" in report_data