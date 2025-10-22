"""
End-to-end tests for complete user journeys
Tests real user scenarios from authentication to document processing and AI interactions
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
import uuid
import io
import json
import asyncio
from typing import Dict, List, Any

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteUserJourney:
    """Test suite for complete user journeys and workflows."""
    
    @pytest.mark.asyncio
    async def test_new_user_onboarding_journey(
        self,
        async_client: AsyncClient,
        test_tenant,
        db_session
    ):
        """Test complete new user onboarding journey."""
        
        # Step 1: User Registration
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "tenant_domain": "test.example.com"
        }
        
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json=registration_data
        )
        
        assert register_response.status_code == 201
        register_result = register_response.json()
        
        assert "user_id" in register_result
        assert "verification_required" in register_result
        user_id = register_result["user_id"]
        
        # Step 2: Email Verification (simulate)
        # In real scenario, user would click email link
        verify_response = await async_client.post(
            f"/api/v1/auth/verify-email",
            json={
                "user_id": user_id,
                "verification_code": "mock_verification_code"
            }
        )
        
        assert verify_response.status_code == 200
        
        # Step 3: First Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "tenant_domain": "test.example.com"
            }
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        
        assert "access_token" in login_result
        assert "refresh_token" in login_result
        access_token = login_result["access_token"]
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Tenant-ID": test_tenant.id
        }
        
        # Step 4: Complete Profile Setup
        profile_response = await async_client.put(
            "/api/v1/users/profile",
            json={
                "preferences": {
                    "language": "en",
                    "theme": "light",
                    "notifications": True,
                    "ai_assistance_level": "intermediate"
                },
                "interests": ["artificial intelligence", "machine learning", "data science"]
            },
            headers=headers
        )
        
        assert profile_response.status_code == 200
        
        # Step 5: Take Platform Tour (API endpoints)
        tour_steps = [
            "/api/v1/tour/dashboard",
            "/api/v1/tour/documents", 
            "/api/v1/tour/search",
            "/api/v1/tour/ai-features",
            "/api/v1/tour/collections"
        ]
        
        for step in tour_steps:
            tour_response = await async_client.get(step, headers=headers)
            assert tour_response.status_code == 200
        
        # Step 6: Mark Tour as Completed
        tour_complete_response = await async_client.post(
            "/api/v1/tour/complete",
            headers=headers
        )
        
        assert tour_complete_response.status_code == 200
        
        # Step 7: Verify User Dashboard Access
        dashboard_response = await async_client.get(
            "/api/v1/dashboard",
            headers=headers
        )
        
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        assert "welcome_message" in dashboard_data
        assert "quick_actions" in dashboard_data
        assert "recent_activity" in dashboard_data
    
    @pytest.mark.asyncio
    async def test_document_research_workflow(
        self,
        async_client: AsyncClient,
        test_user,
        authenticated_headers
    ):
        """Test complete document research workflow."""
        
        # Step 1: Create Research Collection
        collection_response = await async_client.post(
            "/api/v1/collections",
            json={
                "name": "AI Research Collection",
                "description": "Collection for AI research papers and documents",
                "settings": {
                    "public": False,
                    "collaborative": True,
                    "auto_categorize": True,
                    "ai_assistance": True
                }
            },
            headers=authenticated_headers
        )
        
        assert collection_response.status_code == 201
        collection_data = collection_response.json()
        collection_id = collection_data["id"]
        
        # Step 2: Upload Multiple Research Documents
        documents = []
        
        for i, topic in enumerate(["neural_networks", "deep_learning", "nlp"], 1):
            content = f"Research paper about {topic.replace('_', ' ')}. " \
                     f"This document covers fundamental concepts, methodologies, " \
                     f"and applications in {topic.replace('_', ' ')}."
            
            upload_response = await async_client.post(
                "/api/v1/documents/upload",
                data={
                    "title": f"{topic.replace('_', ' ').title()} Research Paper",
                    "collection_id": collection_id,
                    "auto_process": True,
                    "extract_citations": True
                },
                files={
                    "file": (f"{topic}.pdf", io.BytesIO(content.encode()), "application/pdf")
                },
                headers=authenticated_headers
            )
            
            assert upload_response.status_code == 201
            documents.append(upload_response.json())
        
        # Wait for processing simulation
        await asyncio.sleep(1)
        
        # Step 3: Verify All Documents Are Processed
        for doc in documents:
            status_response = await async_client.get(
                f"/api/v1/documents/{doc['document_id']}/status",
                headers=authenticated_headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] in ["processed", "processing"]
        
        # Step 4: Perform Research Queries
        research_queries = [
            "What are the main types of neural networks?",
            "How does deep learning differ from traditional machine learning?",
            "What are the applications of natural language processing?",
            "Compare different neural network architectures"
        ]
        
        research_results = []
        
        for query in research_queries:
            rag_response = await async_client.post(
                "/api/v1/rag/query",
                json={
                    "question": query,
                    "collection_ids": [collection_id],
                    "mode": "research",
                    "max_citations": 5,
                    "include_metadata": True,
                    "generate_follow_ups": True
                },
                headers=authenticated_headers
            )
            
            assert rag_response.status_code == 200
            result = rag_response.json()
            
            assert "answer" in result
            assert "citations" in result
            assert "follow_up_questions" in result
            assert len(result["citations"]) > 0
            
            research_results.append(result)
        
        # Step 5: Create Research Summary
        summary_response = await async_client.post(
            "/api/v1/ai/summarize-collection",
            json={
                "collection_id": collection_id,
                "summary_type": "research_overview",
                "include_key_themes": True,
                "include_relationships": True
            },
            headers=authenticated_headers
        )
        
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        
        assert "summary" in summary_data
        assert "key_themes" in summary_data
        assert "document_relationships" in summary_data
        
        # Step 6: Generate Research Report
        report_response = await async_client.post(
            "/api/v1/reports/generate",
            json={
                "type": "research_report",
                "collection_id": collection_id,
                "queries": research_queries,
                "include_citations": True,
                "format": "markdown"
            },
            headers=authenticated_headers
        )
        
        assert report_response.status_code == 200
        report_data = report_response.json()
        
        assert "report_id" in report_data
        assert "download_url" in report_data
        
        # Step 7: Export Research Data
        export_response = await async_client.post(
            "/api/v1/collections/{collection_id}/export",
            json={
                "format": "research_package",
                "include_documents": True,
                "include_queries": True,
                "include_summaries": True
            },
            headers=authenticated_headers
        )
        
        assert export_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_collaborative_document_workflow(
        self,
        async_client: AsyncClient,
        test_user,
        test_admin_user,
        authenticated_headers,
        admin_headers,
        db_session
    ):
        """Test collaborative document workflow with multiple users."""
        
        # Step 1: User 1 creates shared collection
        collection_response = await async_client.post(
            "/api/v1/collections",
            json={
                "name": "Shared Project Collection",
                "description": "Collaborative collection for team project",
                "settings": {
                    "public": False,
                    "collaborative": True,
                    "require_approval": False
                }
            },
            headers=authenticated_headers
        )
        
        assert collection_response.status_code == 201
        collection_id = collection_response.json()["id"]
        
        # Step 2: User 1 invites User 2 to collection
        invite_response = await async_client.post(
            f"/api/v1/collections/{collection_id}/invite",
            json={
                "user_id": test_admin_user.id,
                "permission_level": "editor",
                "send_notification": True
            },
            headers=authenticated_headers
        )
        
        assert invite_response.status_code == 200
        
        # Step 3: User 2 accepts invitation
        accept_response = await async_client.post(
            f"/api/v1/collections/{collection_id}/join",
            headers=admin_headers
        )
        
        assert accept_response.status_code == 200
        
        # Step 4: User 1 uploads document
        doc1_response = await async_client.post(
            "/api/v1/documents/upload",
            data={
                "title": "Project Requirements Document",
                "collection_id": collection_id,
                "auto_process": True
            },
            files={
                "file": ("requirements.txt", io.BytesIO(b"Project requirements content"), "text/plain")
            },
            headers=authenticated_headers
        )
        
        assert doc1_response.status_code == 201
        doc1_id = doc1_response.json()["document_id"]
        
        # Step 5: User 2 uploads document
        doc2_response = await async_client.post(
            "/api/v1/documents/upload",
            data={
                "title": "Technical Specification",
                "collection_id": collection_id,
                "auto_process": True
            },
            files={
                "file": ("spec.txt", io.BytesIO(b"Technical specification content"), "text/plain")
            },
            headers=admin_headers
        )
        
        assert doc2_response.status_code == 201
        doc2_id = doc2_response.json()["document_id"]
        
        # Step 6: User 1 adds comments to User 2's document
        comment_response = await async_client.post(
            f"/api/v1/documents/{doc2_id}/comments",
            json={
                "content": "Great technical specification! I have a few suggestions...",
                "type": "general_comment",
                "metadata": {"section": "introduction"}
            },
            headers=authenticated_headers
        )
        
        assert comment_response.status_code == 201
        
        # Step 7: User 2 responds to comment
        reply_response = await async_client.post(
            f"/api/v1/documents/{doc2_id}/comments",
            json={
                "content": "Thanks for the feedback! I'll incorporate your suggestions.",
                "type": "reply",
                "parent_comment_id": comment_response.json()["comment_id"]
            },
            headers=admin_headers
        )
        
        assert reply_response.status_code == 201
        
        # Step 8: Collaborative AI Query
        collab_query_response = await async_client.post(
            "/api/v1/rag/query",
            json={
                "question": "What are the main requirements and how do they align with the technical specification?",
                "collection_ids": [collection_id],
                "mode": "comparison",
                "collaborative": True,
                "include_all_perspectives": True
            },
            headers=authenticated_headers
        )
        
        assert collab_query_response.status_code == 200
        collab_result = collab_query_response.json()
        
        assert "answer" in collab_result
        assert "comparison_table" in collab_result
        assert "perspectives" in collab_result
        
        # Step 9: Generate Collaboration Report
        collab_report_response = await async_client.get(
            f"/api/v1/collections/{collection_id}/collaboration-report",
            headers=authenticated_headers
        )
        
        assert collab_report_response.status_code == 200
        collab_data = collab_report_response.json()
        
        assert "contributors" in collab_data
        assert "activity_timeline" in collab_data
        assert "document_interactions" in collab_data
        assert len(collab_data["contributors"]) == 2
    
    @pytest.mark.asyncio
    async def test_ai_assistant_workflow(
        self,
        async_client: AsyncClient,
        test_user,
        authenticated_headers
    ):
        """Test comprehensive AI assistant workflow."""
        
        # Step 1: Start AI Chat Session
        chat_response = await async_client.post(
            "/api/v1/chat/sessions",
            json={
                "mode": "assistant",
                "context": "document_analysis",
                "preferences": {
                    "response_style": "detailed",
                    "include_citations": True,
                    "language": "en"
                }
            },
            headers=authenticated_headers
        )
        
        assert chat_response.status_code == 201
        session_data = chat_response.json()
        session_id = session_data["session_id"]
        
        # Step 2: Upload Document for Analysis
        doc_response = await async_client.post(
            "/api/v1/documents/upload",
            data={
                "title": "Financial Report Q4 2023",
                "auto_process": True,
                "ai_analysis": True
            },
            files={
                "file": ("financial_report.pdf", io.BytesIO(b"Financial report content with revenue, expenses, and projections"), "application/pdf")
            },
            headers=authenticated_headers
        )
        
        assert doc_response.status_code == 201
        doc_id = doc_response.json()["document_id"]
        
        # Step 3: AI Document Analysis
        analysis_response = await async_client.post(
            "/api/v1/ai/analyze-document",
            json={
                "document_id": doc_id,
                "analysis_types": [
                    "summary",
                    "key_insights", 
                    "sentiment_analysis",
                    "entity_extraction",
                    "trend_analysis"
                ]
            },
            headers=authenticated_headers
        )
        
        assert analysis_response.status_code == 200
        analysis_data = analysis_response.json()
        
        assert "summary" in analysis_data
        assert "key_insights" in analysis_data
        assert "entities" in analysis_data
        
        # Step 4: Interactive Q&A with AI
        qa_conversations = [
            "What are the key financial highlights from this report?",
            "What trends do you see in the revenue data?",
            "Are there any concerning areas I should focus on?",
            "What recommendations would you make based on this analysis?"
        ]
        
        conversation_history = []
        
        for question in qa_conversations:
            message_response = await async_client.post(
                f"/api/v1/chat/sessions/{session_id}/messages",
                json={
                    "message": question,
                    "context_document_ids": [doc_id],
                    "use_document_context": True
                },
                headers=authenticated_headers
            )
            
            assert message_response.status_code == 200
            message_data = message_response.json()
            
            assert "response" in message_data
            assert "citations" in message_data
            conversation_history.append(message_data)
        
        # Step 5: Generate AI Insights Report
        insights_response = await async_client.post(
            "/api/v1/ai/generate-insights",
            json={
                "session_id": session_id,
                "document_ids": [doc_id],
                "insight_types": [
                    "executive_summary",
                    "actionable_recommendations", 
                    "risk_assessment",
                    "opportunities"
                ]
            },
            headers=authenticated_headers
        )
        
        assert insights_response.status_code == 200
        insights_data = insights_response.json()
        
        assert "executive_summary" in insights_data
        assert "recommendations" in insights_data
        assert "risk_assessment" in insights_data
        
        # Step 6: AI-Powered Follow-up Actions
        actions_response = await async_client.post(
            "/api/v1/ai/suggest-actions",
            json={
                "context": "financial_analysis",
                "document_id": doc_id,
                "conversation_history": conversation_history[-2:],  # Last 2 interactions
                "user_role": "analyst"
            },
            headers=authenticated_headers
        )
        
        assert actions_response.status_code == 200
        actions_data = actions_response.json()
        
        assert "suggested_actions" in actions_data
        assert len(actions_data["suggested_actions"]) > 0
        
        # Step 7: Schedule AI Follow-up
        schedule_response = await async_client.post(
            "/api/v1/ai/schedule-followup",
            json={
                "session_id": session_id,
                "followup_type": "monthly_analysis",
                "schedule": "monthly",
                "next_execution": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "context": {
                    "document_types": ["financial_report"],
                    "analysis_focus": ["trends", "recommendations"]
                }
            },
            headers=authenticated_headers
        )
        
        assert schedule_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_enterprise_compliance_workflow(
        self,
        async_client: AsyncClient,
        test_admin_user,
        admin_headers
    ):
        """Test enterprise compliance and audit workflow."""
        
        # Step 1: Set Up Compliance Policies
        policy_response = await async_client.post(
            "/api/v1/compliance/policies",
            json={
                "name": "Data Protection Policy",
                "type": "data_protection",
                "rules": [
                    {
                        "type": "pii_detection",
                        "action": "flag_and_notify",
                        "severity": "high"
                    },
                    {
                        "type": "retention_period",
                        "value": 2555,  # 7 years in days
                        "auto_delete": False
                    },
                    {
                        "type": "access_logging",
                        "level": "detailed",
                        "retention_days": 90
                    }
                ],
                "applies_to": ["all_documents"],
                "effective_date": datetime.utcnow().isoformat()
            },
            headers=admin_headers
        )
        
        assert policy_response.status_code == 201
        policy_id = policy_response.json()["policy_id"]
        
        # Step 2: Upload Document with PII (trigger compliance scan)
        sensitive_doc_response = await async_client.post(
            "/api/v1/documents/upload",
            data={
                "title": "Employee Data Report",
                "auto_process": True,
                "compliance_scan": True
            },
            files={
                "file": ("employee_data.txt", 
                        io.BytesIO(b"Employee John Doe, SSN: 123-45-6789, Email: john@company.com"), 
                        "text/plain")
            },
            headers=admin_headers
        )
        
        assert sensitive_doc_response.status_code == 201
        sensitive_doc_id = sensitive_doc_response.json()["document_id"]
        
        # Step 3: Check Compliance Scan Results
        compliance_response = await async_client.get(
            f"/api/v1/documents/{sensitive_doc_id}/compliance",
            headers=admin_headers
        )
        
        assert compliance_response.status_code == 200
        compliance_data = compliance_response.json()
        
        assert "pii_detected" in compliance_data
        assert "compliance_violations" in compliance_data
        assert "risk_score" in compliance_data
        
        # Step 4: Generate Audit Report
        audit_response = await async_client.post(
            "/api/v1/compliance/audit-report",
            json={
                "report_type": "comprehensive",
                "date_range": {
                    "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                },
                "include_sections": [
                    "data_access_logs",
                    "compliance_violations",
                    "user_activity",
                    "document_processing",
                    "ai_interactions"
                ]
            },
            headers=admin_headers
        )
        
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        
        assert "report_id" in audit_data
        assert "sections" in audit_data
        assert "summary" in audit_data
        
        # Step 5: Export Compliance Data for External Audit
        export_response = await async_client.post(
            "/api/v1/compliance/export",
            json={
                "export_type": "audit_package",
                "format": "encrypted_zip",
                "include_logs": True,
                "include_policies": True,
                "include_violations": True,
                "date_range": {
                    "start": (datetime.utcnow() - timedelta(days=90)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            },
            headers=admin_headers
        )
        
        assert export_response.status_code == 200
        export_data = export_response.json()
        
        assert "export_id" in export_data
        assert "download_url" in export_data
        assert "encryption_key" in export_data
    
    @pytest.mark.asyncio
    async def test_performance_stress_workflow(
        self,
        async_client: AsyncClient,
        test_user,
        authenticated_headers
    ):
        """Test system performance under load."""
        
        # Step 1: Create Multiple Collections
        collections = []
        for i in range(5):
            collection_response = await async_client.post(
                "/api/v1/collections",
                json={
                    "name": f"Performance Test Collection {i+1}",
                    "description": f"Collection for performance testing {i+1}"
                },
                headers=authenticated_headers
            )
            
            assert collection_response.status_code == 201
            collections.append(collection_response.json()["id"])
        
        # Step 2: Upload Multiple Documents Concurrently
        upload_tasks = []
        
        for i in range(20):
            content = f"Performance test document {i+1} content. " \
                     f"This document contains information about testing, " \
                     f"performance, scalability, and system reliability."
            
            collection_id = collections[i % len(collections)]
            
            upload_task = async_client.post(
                "/api/v1/documents/upload",
                data={
                    "title": f"Performance Test Doc {i+1}",
                    "collection_id": collection_id,
                    "auto_process": True
                },
                files={
                    "file": (f"perf_doc_{i+1}.txt", io.BytesIO(content.encode()), "text/plain")
                },
                headers=authenticated_headers
            )
            
            upload_tasks.append(upload_task)
        
        # Execute uploads concurrently
        upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
        
        # Verify most uploads succeeded
        successful_uploads = [r for r in upload_results if not isinstance(r, Exception)]
        assert len(successful_uploads) >= 15  # Allow some failures under load
        
        # Step 3: Perform Concurrent Search Queries
        search_queries = [
            "performance testing",
            "system reliability", 
            "scalability metrics",
            "document processing",
            "content analysis"
        ]
        
        search_tasks = []
        for query in search_queries:
            for _ in range(4):  # 4 concurrent searches per query
                search_task = async_client.post(
                    "/api/v1/search/hybrid",
                    json={
                        "query": query,
                        "limit": 10
                    },
                    headers=authenticated_headers
                )
                search_tasks.append(search_task)
        
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        successful_searches = [r for r in search_results if not isinstance(r, Exception)]
        assert len(successful_searches) >= 15  # Allow some failures under load
        
        # Step 4: Concurrent RAG Queries
        rag_tasks = []
        rag_questions = [
            "What is performance testing?",
            "How do you measure system reliability?",
            "What are scalability best practices?",
            "Explain document processing workflows"
        ]
        
        for question in rag_questions:
            for _ in range(3):  # 3 concurrent RAG queries per question
                rag_task = async_client.post(
                    "/api/v1/rag/query",
                    json={
                        "question": question,
                        "mode": "standard",
                        "max_citations": 3
                    },
                    headers=authenticated_headers
                )
                rag_tasks.append(rag_task)
        
        rag_results = await asyncio.gather(*rag_tasks, return_exceptions=True)
        successful_rag = [r for r in rag_results if not isinstance(r, Exception)]
        assert len(successful_rag) >= 8  # Allow some failures under load
        
        # Step 5: Check System Health After Load
        health_response = await async_client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        
        # System should still be responsive
        assert health_data["system"]["cpu_percent"] < 90
        assert health_data["system"]["memory_percent"] < 90