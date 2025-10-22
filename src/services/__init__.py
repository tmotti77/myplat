"""Core services for the RAG platform."""

from .cache import CacheService, cache_service
from .storage import StorageService, storage_service
from .embedding_service import embedding_service

# TODO: Implement these services as needed
# from .embedding import EmbeddingService, embedding_service
# from .vector_store import VectorStoreService, vector_store_service
# from .search import SearchService, search_service
# from .llm_router import LLMRouterService, llm_router_service
# from .rag_engine import RAGEngine, rag_engine
# from .ingestion import IngestionService, ingestion_service
# from .personalization import PersonalizationService, personalization_service

__all__ = [
    "CacheService", "cache_service",
    "StorageService", "storage_service", 
    "embedding_service",
    # TODO: Add these as they are implemented
    # "EmbeddingService", "embedding_service",
    # "VectorStoreService", "vector_store_service",
    # "SearchService", "search_service",
    # "LLMRouterService", "llm_router_service",
    # "RAGEngine", "rag_engine",
    # "IngestionService", "ingestion_service",
    # "PersonalizationService", "personalization_service",
]