"""Preference pair models for DPO training."""
from enum import Enum
from sqlalchemy import Column, String, Float, JSON

from src.models.base import BaseModel


class PreferenceOutcome(str, Enum):
    """Preference outcomes for comparison."""
    PREFERRED_A = "preferred_a"
    PREFERRED_B = "preferred_b"
    TIE = "tie"
    INVALID = "invalid"


class PreferencePair(BaseModel):
    """Model for preference pairs used in DPO training."""
    
    __tablename__ = "preference_pairs"
    
    # Core identification
    user_id = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    
    # Query context
    query = Column(String, nullable=False)
    query_context = Column(JSON, default={})
    
    # Response pair
    response_a_id = Column(String, nullable=False, index=True)
    response_b_id = Column(String, nullable=False, index=True)
    
    # Preference data
    preference_outcome = Column(String, nullable=False, index=True)
    preference_strength = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Qualitative feedback
    reasoning = Column(String, nullable=True)
    criteria_used = Column(JSON, default=[])
    
    # Quality and validation
    confidence_score = Column(Float, default=0.5)
    validated = Column(String, default="false")  # Boolean as string
    validation_score = Column(Float, nullable=True)
    
    # Training usage
    used_in_training = Column(String, default="false")  # Boolean as string
    training_run_ids = Column(JSON, default=[])
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def mark_as_used_in_training(self, training_run_id: str):
        """Mark this pair as used in training."""
        self.used_in_training = "true"
        if not self.training_run_ids:
            self.training_run_ids = []
        if training_run_id not in self.training_run_ids:
            self.training_run_ids.append(training_run_id)
    
    def validate(self, score: float):
        """Mark as validated with a score."""
        self.validated = "true"
        self.validation_score = score
    
    @property
    def is_validated(self) -> bool:
        """Check if pair is validated."""
        return self.validated == "true"
    
    @property
    def is_high_quality(self) -> bool:
        """Check if pair is high quality for training."""
        return (
            self.preference_strength >= 0.7 and
            self.confidence_score >= 0.6 and
            self.preference_outcome != PreferenceOutcome.TIE.value
        )