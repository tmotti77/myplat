"""Database models for the hybrid RAG platform."""

from .base import Base
from .tenant import Tenant, TenantPlan, TenantStatus
from .user import User, UserRole, UserStatus
from .source import Source, SourceKind, SourceStatus, CrawlFrequency
from .document import Document, DocumentStatus, DocumentType
from .chunk import Chunk, ChunkType
from .embedding import Embedding, EmbeddingModel, EmbeddingStatus
from .retrieval import RetrievalEvent, RetrievalMethod
from .answer import Answer, AnswerStatus, AnswerType, ConfidenceLevel
from .citation import Citation, CitationType
from .profile import Profile, PreferenceType, ContentDepth, ResponseStyle
from .expert import Expert, ExpertStatus, ExpertLevel, ReputationEvent, ReputationEventType
from .feedback import Feedback, FeedbackSignal, FeedbackReason, FeedbackStatus
from .experiment import Experiment, ExperimentStatus, ExperimentType, VariantType

# Export all models for easy import
__all__ = [
    # Base
    "Base",
    
    # Tenant and User models
    "Tenant", "TenantPlan", "TenantStatus",
    "User", "UserRole", "UserStatus",
    
    # Content models
    "Source", "SourceKind", "SourceStatus", "CrawlFrequency",
    "Document", "DocumentStatus", "DocumentType",
    "Chunk", "ChunkType",
    "Embedding", "EmbeddingModel", "EmbeddingStatus",
    
    # Retrieval and answers
    "RetrievalEvent", "RetrievalMethod",
    "Answer", "AnswerStatus", "AnswerType", "ConfidenceLevel",
    "Citation", "CitationType",
    
    # Personalization
    "Profile", "PreferenceType", "ContentDepth", "ResponseStyle",
    
    # Expert system
    "Expert", "ExpertStatus", "ExpertLevel",
    "ReputationEvent", "ReputationEventType",
    
    # Feedback and experiments
    "Feedback", "FeedbackSignal", "FeedbackReason", "FeedbackStatus",
    "Experiment", "ExperimentStatus", "ExperimentType", "VariantType",
]