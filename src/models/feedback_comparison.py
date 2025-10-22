"""Feedback comparison models for preference learning."""
from enum import Enum
from sqlalchemy import Column, String, Float, JSON

from src.models.base import BaseModel


class ComparisonType(str, Enum):
    """Types of comparisons."""
    RESPONSE_QUALITY = "response_quality"
    ACCURACY = "accuracy"
    HELPFULNESS = "helpfulness"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    COMPLETENESS = "completeness"
    BIAS_ASSESSMENT = "bias_assessment"


class FeedbackComparison(BaseModel):
    """Model for comparative feedback between content items."""
    
    __tablename__ = "feedback_comparisons"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Comparison details
    comparison_type = Column(String, nullable=False)
    
    # Items being compared
    item_a_id = Column(String, nullable=False, index=True)
    item_b_id = Column(String, nullable=False, index=True)
    item_type = Column(String, nullable=False)  # response, document, etc.
    
    # Comparison result
    preference = Column(String, nullable=False)  # "a", "b", "tie"
    confidence = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Context
    query_context = Column(String, nullable=True)
    comparison_criteria = Column(JSON, default=[])
    
    # Reasoning
    reasoning = Column(String, nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)