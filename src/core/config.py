"""Configuration management for the RAG platform."""
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = Field(default="Hybrid RAG Platform", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    APP_DESCRIPTION: str = Field(default="Production-ready hybrid RAG AI platform", env="APP_DESCRIPTION")
    APP_HOST: str = Field(default="0.0.0.0", env="APP_HOST")
    APP_PORT: int = Field(default=8000, env="APP_PORT")
    APP_DEBUG: bool = Field(default=False, env="APP_DEBUG")
    APP_RELOAD: bool = Field(default=False, env="APP_RELOAD")
    
    # Database
    DATABASE_URL: PostgresDsn = Field(env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=0, env="DATABASE_MAX_OVERFLOW")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    REDIS_URL: RedisDsn = Field(env="REDIS_URL")
    REDIS_POOL_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_POOL_MAX_CONNECTIONS")
    
    # Vector Database
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    QDRANT_TIMEOUT: int = Field(default=60, env="QDRANT_TIMEOUT")
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    ELASTICSEARCH_USERNAME: Optional[str] = Field(default=None, env="ELASTICSEARCH_USERNAME")
    ELASTICSEARCH_PASSWORD: Optional[str] = Field(default=None, env="ELASTICSEARCH_PASSWORD")
    
    # Object Storage (MinIO/S3)
    MINIO_ENDPOINT: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(env="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")
    MINIO_BUCKET_NAME: str = Field(default="rag-documents", env="MINIO_BUCKET_NAME")
    
    # File Storage
    UPLOAD_DIR: str = Field(default="/app/uploads", env="UPLOAD_DIR")
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    COHERE_API_KEY: Optional[str] = Field(default=None, env="COHERE_API_KEY")
    
    # Authentication
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    REFRESH_TOKEN_EXPIRATION_DAYS: int = Field(default=30, env="REFRESH_TOKEN_EXPIRATION_DAYS")
    
    # OAuth Configuration
    OAUTH_CLIENT_ID: Optional[str] = Field(default=None, env="OAUTH_CLIENT_ID")
    OAUTH_CLIENT_SECRET: Optional[str] = Field(default=None, env="OAUTH_CLIENT_SECRET")
    OAUTH_DOMAIN: Optional[str] = Field(default=None, env="OAUTH_DOMAIN")
    OAUTH_AUDIENCE: Optional[str] = Field(default=None, env="OAUTH_AUDIENCE")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ENCRYPTION_KEY: str = Field(env="ENCRYPTION_KEY")
    MASTER_ENCRYPTION_KEY: Optional[str] = Field(default=None, env="MASTER_ENCRYPTION_KEY")
    HASH_ALGORITHM: str = Field(default="argon2", env="HASH_ALGORITHM")
    JWT_REFRESH_SECRET_KEY: str = Field(env="JWT_REFRESH_SECRET_KEY")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # Enhanced Security Settings
    ENCRYPTION_ENABLED: bool = Field(default=True, env="ENCRYPTION_ENABLED")
    ENCRYPTION_ALGORITHM: str = Field(default="AES-256-GCM", env="ENCRYPTION_ALGORITHM")
    KEY_ROTATION_INTERVAL_DAYS: int = Field(default=90, env="KEY_ROTATION_INTERVAL_DAYS")
    
    # Session Management
    SESSION_TIMEOUT_MINUTES: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    MAX_CONCURRENT_SESSIONS: int = Field(default=5, env="MAX_CONCURRENT_SESSIONS")
    SESSION_SECURITY_ENABLED: bool = Field(default=True, env="SESSION_SECURITY_ENABLED")
    
    # Audit and Compliance
    AUDIT_ENABLED: bool = Field(default=True, env="AUDIT_ENABLED")
    AUDIT_RETENTION_DAYS: int = Field(default=2555, env="AUDIT_RETENTION_DAYS")
    COMPLIANCE_MODE: str = Field(default="standard", env="COMPLIANCE_MODE")
    
    # Privacy and Data Protection
    GDPR_COMPLIANCE_ENABLED: bool = Field(default=True, env="GDPR_COMPLIANCE_ENABLED")
    CCPA_COMPLIANCE_ENABLED: bool = Field(default=True, env="CCPA_COMPLIANCE_ENABLED")
    HIPAA_COMPLIANCE_ENABLED: bool = Field(default=False, env="HIPAA_COMPLIANCE_ENABLED")
    PII_DETECTION_ENABLED: bool = Field(default=True, env="PII_DETECTION_ENABLED")
    PII_ANONYMIZATION_ENABLED: bool = Field(default=True, env="PII_ANONYMIZATION_ENABLED")
    
    # Data Retention
    DEFAULT_DATA_RETENTION_DAYS: int = Field(default=2555, env="DEFAULT_DATA_RETENTION_DAYS")
    AUTOMATIC_DATA_CLEANUP_ENABLED: bool = Field(default=True, env="AUTOMATIC_DATA_CLEANUP_ENABLED")
    DATA_EXPORT_ENABLED: bool = Field(default=True, env="DATA_EXPORT_ENABLED")
    
    # Security Monitoring
    SECURITY_MONITORING_ENABLED: bool = Field(default=True, env="SECURITY_MONITORING_ENABLED")
    ANOMALY_DETECTION_ENABLED: bool = Field(default=True, env="ANOMALY_DETECTION_ENABLED")
    SECURITY_ALERTS_ENABLED: bool = Field(default=True, env="SECURITY_ALERTS_ENABLED")
    INTRUSION_DETECTION_ENABLED: bool = Field(default=True, env="INTRUSION_DETECTION_ENABLED")
    
    # Access Control
    RBAC_ENABLED: bool = Field(default=True, env="RBAC_ENABLED")
    ABAC_ENABLED: bool = Field(default=True, env="ABAC_ENABLED")
    MFA_ENABLED: bool = Field(default=False, env="MFA_ENABLED")
    MFA_REQUIRED_FOR_ADMIN: bool = Field(default=True, env="MFA_REQUIRED_FOR_ADMIN")
    
    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    OTEL_SERVICE_NAME: str = Field(default="rag-platform", env="OTEL_SERVICE_NAME")
    OTEL_RESOURCE_ATTRIBUTES: str = Field(
        default="service.version=1.0.0",
        env="OTEL_RESOURCE_ATTRIBUTES"
    )
    PROMETHEUS_GATEWAY: str = Field(default="localhost:9090", env="PROMETHEUS_GATEWAY")
    JAEGER_AGENT_HOST: str = Field(default="localhost", env="JAEGER_AGENT_HOST")
    JAEGER_AGENT_PORT: int = Field(default=6831, env="JAEGER_AGENT_PORT")
    
    # Enhanced Observability
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    ENABLE_TRACING: bool = Field(default=True, env="ENABLE_TRACING")
    ENABLE_PROMETHEUS: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    METRICS_PORT: int = Field(default=8000, env="METRICS_PORT")
    
    # Distributed Tracing
    JAEGER_ENABLED: bool = Field(default=True, env="JAEGER_ENABLED")
    JAEGER_ENDPOINT: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    JAEGER_HOST: str = Field(default="localhost", env="JAEGER_HOST")
    JAEGER_PORT: int = Field(default=6831, env="JAEGER_PORT")
    
    # Environment and Versioning
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    LOG_ROTATION: str = Field(default="1 day", env="LOG_ROTATION")
    LOG_RETENTION: str = Field(default="30 days", env="LOG_RETENTION")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=200, env="RATE_LIMIT_BURST")
    
    # Embedding Models
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSIONS: int = Field(default=3072, env="EMBEDDING_DIMENSIONS")
    LOCAL_EMBEDDING_MODEL: str = Field(default="BAAI/bge-m3", env="LOCAL_EMBEDDING_MODEL")
    RE_RANKING_MODEL: str = Field(default="BAAI/bge-reranker-large", env="RE_RANKING_MODEL")
    
    # Document Processing
    MAX_FILE_SIZE_MB: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "he", "ar", "es", "fr", "de"],
        env="SUPPORTED_LANGUAGES"
    )
    CHUNK_SIZE: int = Field(default=600, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=100, env="CHUNK_OVERLAP")
    MAX_CHUNKS_PER_DOCUMENT: int = Field(default=1000, env="MAX_CHUNKS_PER_DOCUMENT")
    
    # LLM Configuration
    DEFAULT_LLM_MODEL: str = Field(default="gpt-4-turbo-preview", env="DEFAULT_LLM_MODEL")
    FALLBACK_LLM_MODEL: str = Field(default="gpt-3.5-turbo", env="FALLBACK_LLM_MODEL")
    MAX_TOKENS: int = Field(default=4000, env="MAX_TOKENS")
    TEMPERATURE: float = Field(default=0.1, env="TEMPERATURE")
    TOP_P: float = Field(default=0.9, env="TOP_P")
    
    # Cost Management
    MAX_COST_PER_QUERY_USD: float = Field(default=0.10, env="MAX_COST_PER_QUERY_USD")
    DAILY_COST_LIMIT_USD: float = Field(default=100.00, env="DAILY_COST_LIMIT_USD")
    MONTHLY_COST_LIMIT_USD: float = Field(default=3000.00, env="MONTHLY_COST_LIMIT_USD")
    
    # Multi-tenancy
    MULTI_TENANT_MODE: bool = Field(default=True, env="MULTI_TENANT_MODE")
    DEFAULT_TENANT_PLAN: str = Field(default="basic", env="DEFAULT_TENANT_PLAN")
    MAX_DOCUMENTS_PER_TENANT: int = Field(default=10000, env="MAX_DOCUMENTS_PER_TENANT")
    MAX_QUERIES_PER_DAY: int = Field(default=1000, env="MAX_QUERIES_PER_DAY")
    
    # Background Tasks
    CELERY_BROKER_URL: str = Field(env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(env="CELERY_RESULT_BACKEND")
    CELERY_TASK_SERIALIZER: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    CELERY_TIMEZONE: str = Field(default="UTC", env="CELERY_TIMEZONE")
    
    # Monitoring and Health Checks
    HEALTH_CHECK_INTERVAL: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    METRICS_COLLECTION_INTERVAL: int = Field(default=60, env="METRICS_COLLECTION_INTERVAL")
    
    # Feature Flags
    ENABLE_REAL_TIME_UPDATES: bool = Field(default=True, env="ENABLE_REAL_TIME_UPDATES")
    ENABLE_ADVANCED_ANALYTICS: bool = Field(default=True, env="ENABLE_ADVANCED_ANALYTICS")
    ENABLE_EXPERT_SYSTEM: bool = Field(default=True, env="ENABLE_EXPERT_SYSTEM")
    ENABLE_FEEDBACK_LEARNING: bool = Field(default=True, env="ENABLE_FEEDBACK_LEARNING")
    ENABLE_COST_OPTIMIZATION: bool = Field(default=True, env="ENABLE_COST_OPTIMIZATION")
    
    # Development/Testing
    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: Optional[PostgresDsn] = Field(default=None, env="TEST_DATABASE_URL")
    MOCK_LLM_RESPONSES: bool = Field(default=False, env="MOCK_LLM_RESPONSES")
    SKIP_EMBEDDINGS: bool = Field(default=False, env="SKIP_EMBEDDINGS")
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("SUPPORTED_LANGUAGES", mode="before")
    @classmethod
    def assemble_supported_languages(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse supported languages from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("CELERY_ACCEPT_CONTENT", mode="before")
    @classmethod
    def assemble_celery_accept_content(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse Celery accept content from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }
        
    # Computed properties
    @property
    def DATABASE_CONFIG(self) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "url": str(self.DATABASE_URL),
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "echo": self.DATABASE_ECHO,
        }
    
    @property
    def REDIS_CONFIG(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {
            "url": str(self.REDIS_URL),
            "max_connections": self.REDIS_POOL_MAX_CONNECTIONS,
        }
    
    @property
    def MINIO_CONFIG(self) -> Dict[str, Any]:
        """Get MinIO configuration."""
        return {
            "endpoint": self.MINIO_ENDPOINT,
            "access_key": self.MINIO_ACCESS_KEY,
            "secret_key": self.MINIO_SECRET_KEY,
            "secure": self.MINIO_SECURE,
            "bucket_name": self.MINIO_BUCKET_NAME,
        }
    
    @property
    def LLM_API_KEYS(self) -> Dict[str, Optional[str]]:
        """Get all LLM API keys."""
        return {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "google": self.GOOGLE_API_KEY,
            "cohere": self.COHERE_API_KEY,
        }
    
    @property
    def DEFAULT_CHUNK_CONFIG(self) -> Dict[str, Any]:
        """Get default chunking configuration."""
        return {
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "max_chunks": self.MAX_CHUNKS_PER_DOCUMENT,
        }
    
    @property
    def DEFAULT_LLM_CONFIG(self) -> Dict[str, Any]:
        """Get default LLM configuration."""
        return {
            "model": self.DEFAULT_LLM_MODEL,
            "fallback_model": self.FALLBACK_LLM_MODEL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
            "top_p": self.TOP_P,
        }
    
    @property
    def COST_LIMITS(self) -> Dict[str, float]:
        """Get cost limit configuration."""
        return {
            "max_cost_per_query": self.MAX_COST_PER_QUERY_USD,
            "daily_limit": self.DAILY_COST_LIMIT_USD,
            "monthly_limit": self.MONTHLY_COST_LIMIT_USD,
        }
    
    @property
    def FEATURE_FLAGS(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return {
            "real_time_updates": self.ENABLE_REAL_TIME_UPDATES,
            "advanced_analytics": self.ENABLE_ADVANCED_ANALYTICS,
            "expert_system": self.ENABLE_EXPERT_SYSTEM,
            "feedback_learning": self.ENABLE_FEEDBACK_LEARNING,
            "cost_optimization": self.ENABLE_COST_OPTIMIZATION,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()