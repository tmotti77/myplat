"""
Pytest configuration and shared fixtures for the Hybrid RAG AI Platform test suite
Provides comprehensive test setup with database, Redis, authentication, and more
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis
from datetime import datetime, timedelta
import uuid
import tempfile
import shutil

# Import app and dependencies
from src.main import app
from src.core.config import settings
from src.core.database import get_db, Base
from src.core.auth import get_current_user, get_current_active_user
from src.core.redis import get_redis_client
from src.models.user import User, UserRole
from src.models.tenant import Tenant
from src.models.document import Document, DocumentStatus, DocumentType
from src.models.collection import Collection
from src.models.citation import Citation
from src.models.feedback import Feedback, FeedbackSignal
from src.services.auth_service import AuthService
from src.services.embedding_service import EmbeddingService
from src.services.llm_router import LLMRouter
from src.services.ingestion_service import IngestionService
from src.services.search_service import SearchService
from src.services.rag_engine import RAGEngine
from src.services.personalization import PersonalizationEngine
from src.services.expert_system import ExpertSystem
from src.services.feedback_system import FeedbackSystem

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_rag_platform"
TEST_SYNC_DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/test_rag_platform"

# Use in-memory SQLite for faster tests when not testing database-specific features
FAST_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Test Redis configuration
TEST_REDIS_URL = "redis://localhost:6379/15"  # Use database 15 for tests

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for anyio."""
    return "asyncio"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine with proper cleanup."""
    if os.getenv("USE_FAST_TESTS", "false").lower() == "true":
        # Use in-memory SQLite for fast tests
        engine = create_async_engine(
            FAST_TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
    else:
        # Use PostgreSQL for comprehensive tests
        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with automatic rollback."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()

@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create test Redis client with automatic cleanup."""
    client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    
    # Clear test database
    await client.flushdb()
    
    yield client
    
    # Cleanup
    await client.flushdb()
    await client.close()

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('src.core.config.settings') as mock:
        mock.SECRET_KEY = "test-secret-key-for-testing-only"
        mock.ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.ENVIRONMENT = "test"
        mock.DEBUG = True
        mock.TESTING = True
        mock.DATABASE_URL = TEST_DATABASE_URL
        mock.REDIS_URL = TEST_REDIS_URL
        mock.OPENAI_API_KEY = "test-openai-key"
        mock.ANTHROPIC_API_KEY = "test-anthropic-key"
        mock.QDRANT_URL = "http://localhost:6333"
        mock.QDRANT_API_KEY = None
        mock.MINIO_ENDPOINT = "localhost:9000"
        mock.MINIO_ACCESS_KEY = "minioadmin"
        mock.MINIO_SECRET_KEY = "minioadmin"
        mock.BUCKET_NAME = "test-documents"
        mock.RATE_LIMIT_PER_MINUTE = 1000
        mock.MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        mock.SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".docx", ".pptx", ".xlsx"]
        yield mock

@pytest.fixture
def test_client(db_session, redis_client, mock_settings):
    """Create test client with dependency overrides."""
    
    def override_get_db():
        return db_session
    
    def override_get_redis():
        return redis_client
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup overrides
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client(db_session, redis_client, mock_settings):
    """Create async test client for advanced testing."""
    
    def override_get_db():
        return db_session
    
    def override_get_redis():
        return redis_client
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Cleanup overrides
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_tenant(db_session) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Test Tenant",
        domain="test.example.com",
        settings={
            "max_users": 100,
            "max_documents": 10000,
            "features": ["rag", "chat", "analytics"],
            "storage_quota_gb": 100
        },
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant

@pytest_asyncio.fixture
async def test_user(db_session, test_tenant) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        full_name="Test User",
        tenant_id=test_tenant.id,
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
        preferences={
            "language": "en",
            "theme": "light",
            "notifications": True
        },
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_admin_user(db_session, test_tenant) -> User:
    """Create a test admin user."""
    user = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        username="adminuser",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        full_name="Admin User",
        tenant_id=test_tenant.id,
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        preferences={
            "language": "en",
            "theme": "dark",
            "notifications": True
        },
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_collection(db_session, test_tenant, test_user) -> Collection:
    """Create a test collection."""
    collection = Collection(
        id=str(uuid.uuid4()),
        name="Test Collection",
        description="A collection for testing",
        tenant_id=test_tenant.id,
        owner_id=test_user.id,
        settings={
            "public": False,
            "collaborative": True,
            "auto_categorize": True
        },
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection

@pytest_asyncio.fixture
async def test_document(db_session, test_tenant, test_user, test_collection) -> Document:
    """Create a test document."""
    document = Document(
        id=str(uuid.uuid4()),
        title="Test Document",
        filename="test_document.pdf",
        file_path="/test/path/test_document.pdf",
        file_size=1024 * 1024,  # 1MB
        file_type=DocumentType.PDF,
        tenant_id=test_tenant.id,
        uploaded_by=test_user.id,
        collection_id=test_collection.id,
        status=DocumentStatus.PROCESSED,
        processing_metadata={
            "text_length": 5000,
            "page_count": 10,
            "language": "en",
            "confidence_score": 0.95
        },
        content="This is test document content for testing purposes.",
        summary="Test document summary",
        keywords=["test", "document", "sample"],
        created_at=datetime.utcnow(),
        processed_at=datetime.utcnow()
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document

@pytest.fixture
def mock_auth_service():
    """Mock authentication service."""
    mock_service = Mock(spec=AuthService)
    mock_service.create_access_token = Mock(return_value="test_access_token")
    mock_service.verify_token = Mock(return_value={"sub": "test_user_id", "tenant_id": "test_tenant_id"})
    mock_service.hash_password = Mock(return_value="hashed_password")
    mock_service.verify_password = Mock(return_value=True)
    return mock_service

@pytest.fixture
def mock_embedding_service():
    """Mock embedding service."""
    mock_service = Mock(spec=EmbeddingService)
    mock_service.generate_embeddings = AsyncMock(return_value=[0.1] * 1536)
    mock_service.generate_query_embedding = AsyncMock(return_value=[0.1] * 1536)
    return mock_service

@pytest.fixture
def mock_llm_router():
    """Mock LLM router."""
    mock_router = Mock(spec=LLMRouter)
    mock_router.route_request = AsyncMock(return_value={
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "response": "This is a test response",
        "cost": 0.001,
        "latency": 0.5
    })
    return mock_router

@pytest.fixture
def mock_ingestion_service():
    """Mock ingestion service."""
    mock_service = Mock(spec=IngestionService)
    mock_service.process_document = AsyncMock(return_value={
        "success": True,
        "extracted_text": "Test document content",
        "metadata": {"page_count": 5, "language": "en"},
        "confidence_score": 0.95
    })
    return mock_service

@pytest.fixture
def mock_search_service():
    """Mock search service."""
    mock_service = Mock(spec=SearchService)
    mock_service.hybrid_search = AsyncMock(return_value=[
        {
            "document_id": "doc_1",
            "chunk_id": "chunk_1",
            "content": "Test content",
            "score": 0.95,
            "metadata": {}
        }
    ])
    return mock_service

@pytest.fixture
def mock_rag_engine():
    """Mock RAG engine."""
    mock_engine = Mock(spec=RAGEngine)
    mock_engine.ask_question = AsyncMock(return_value={
        "answer": "This is a test answer",
        "confidence": 0.9,
        "citations": [
            {
                "chunk_text": "Test citation",
                "source_title": "Test Document",
                "confidence": 0.95
            }
        ],
        "conversation_id": "conv_123"
    })
    return mock_engine

@pytest.fixture
def temp_directory():
    """Create temporary directory for file tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_pdf_file(temp_directory):
    """Create a sample PDF file for testing."""
    # This would normally create a real PDF file
    # For now, we'll create a mock file
    file_path = os.path.join(temp_directory, "sample.pdf")
    with open(file_path, "wb") as f:
        f.write(b"Mock PDF content for testing")
    return file_path

@pytest.fixture
def mock_vectors():
    """Generate mock vector embeddings."""
    return {
        "query_vector": [0.1] * 1536,
        "document_vector": [0.2] * 1536,
        "similarity_threshold": 0.7
    }

@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses for different scenarios."""
    return {
        "summarization": "This is a test summary of the document content.",
        "qa_response": "Based on the provided context, the answer is...",
        "translation": "Esta es una traducción de prueba.",
        "analysis": "The document discusses several key themes including...",
        "error_response": "I'm sorry, I don't have enough information to answer that question."
    }

@pytest.fixture
def authenticated_headers(test_user, mock_auth_service):
    """Generate authentication headers for API tests."""
    token = mock_auth_service.create_access_token(data={"sub": test_user.id})
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": test_user.tenant_id
    }

@pytest.fixture
def admin_headers(test_admin_user, mock_auth_service):
    """Generate admin authentication headers for API tests."""
    token = mock_auth_service.create_access_token(data={"sub": test_admin_user.id})
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": test_admin_user.tenant_id
    }

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    Mock.reset_mock

# Test data factories
class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_user_data(**overrides):
        """Create user test data."""
        default_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User",
            "role": "user"
        }
        return {**default_data, **overrides}
    
    @staticmethod
    def create_document_data(**overrides):
        """Create document test data."""
        default_data = {
            "title": "Test Document",
            "content": "This is test document content",
            "summary": "Test summary",
            "keywords": ["test", "document"],
            "file_type": "pdf"
        }
        return {**default_data, **overrides}
    
    @staticmethod
    def create_collection_data(**overrides):
        """Create collection test data."""
        default_data = {
            "name": "Test Collection",
            "description": "Test collection description",
            "settings": {"public": False}
        }
        return {**default_data, **overrides}

@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory

# Database helpers for testing
@pytest.fixture
def db_helpers(db_session):
    """Database helper functions for tests."""
    
    class DBHelpers:
        def __init__(self, session):
            self.session = session
        
        async def create_user(self, **kwargs):
            """Create a user in the database."""
            user_data = TestDataFactory.create_user_data(**kwargs)
            user = User(**user_data)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        
        async def create_document(self, **kwargs):
            """Create a document in the database."""
            doc_data = TestDataFactory.create_document_data(**kwargs)
            document = Document(**doc_data)
            self.session.add(document)
            await self.session.commit()
            await self.session.refresh(document)
            return document
        
        async def count_records(self, model):
            """Count records in a table."""
            result = await self.session.execute(text(f"SELECT COUNT(*) FROM {model.__tablename__}"))
            return result.scalar()
    
    return DBHelpers(db_session)

# Performance testing helpers
@pytest.fixture
def performance_monitor():
    """Monitor performance during tests."""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        def stop(self):
            self.end_time = time.time()
            self.end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
        
        @property
        def memory_delta(self):
            if self.start_memory and self.end_memory:
                return self.end_memory - self.start_memory
            return None
    
    return PerformanceMonitor

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as authentication related")
    config.addinivalue_line("markers", "database: mark test as database related")
    config.addinivalue_line("markers", "ai: mark test as AI/ML related")
    config.addinivalue_line("markers", "api: mark test as API related")
    config.addinivalue_line("markers", "security: mark test as security related")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)