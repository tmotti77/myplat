"""Experiment model for A/B testing and feature experiments."""
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ExperimentStatus(str, Enum):
    """Experiment status options."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentType(str, Enum):
    """Types of experiments."""
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    FEATURE_FLAG = "feature_flag"
    GRADUAL_ROLLOUT = "gradual_rollout"
    PERSONALIZATION = "personalization"


class VariantType(str, Enum):
    """Types of experiment variants."""
    CONTROL = "control"
    TREATMENT = "treatment"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


class Experiment(Base):
    """A/B testing and experiment tracking."""
    
    # Tenant relationship
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    hypothesis = Column(Text, nullable=False)
    
    # Experiment configuration
    experiment_type = Column(String(50), nullable=False, default=ExperimentType.AB_TEST.value)
    status = Column(String(50), nullable=False, default=ExperimentStatus.DRAFT.value, index=True)
    
    # Timing
    started_at = Column(String(50))  # ISO timestamp
    planned_end_at = Column(String(50))  # ISO timestamp
    actual_end_at = Column(String(50))  # ISO timestamp
    duration_days = Column(Integer, nullable=False, default=14)
    
    # Targeting and allocation
    target_population = Column(JSON, nullable=False, default={})  # Targeting criteria
    traffic_allocation = Column(Float, nullable=False, default=1.0)  # % of traffic to include
    
    # Variants configuration
    variants = Column(JSON, nullable=False, default=[])  # List of variant configs
    variant_weights = Column(JSON, nullable=False, default={})  # Variant -> weight mapping
    
    # Success metrics
    primary_metric = Column(String(100), nullable=False)  # Main metric to optimize
    secondary_metrics = Column(JSON, nullable=False, default=[])  # Additional metrics
    success_criteria = Column(JSON, nullable=False, default={})  # What constitutes success
    
    # Statistical configuration
    significance_level = Column(Float, nullable=False, default=0.05)  # Alpha
    power = Column(Float, nullable=False, default=0.8)  # 1 - Beta
    minimum_effect_size = Column(Float, nullable=False, default=0.05)  # Minimum detectable effect
    minimum_sample_size = Column(Integer, nullable=False, default=1000)
    
    # Current status
    total_participants = Column(Integer, nullable=False, default=0)
    participants_per_variant = Column(JSON, nullable=False, default={})
    
    # Results
    results = Column(JSON, nullable=False, default={})  # Statistical results
    is_significant = Column(Boolean, nullable=False, default=False)
    winning_variant = Column(String(50))  # Variant with best performance
    confidence_interval = Column(JSON, nullable=False, default={})
    
    # Analysis
    analyzed_at = Column(String(50))  # ISO timestamp
    analysis_notes = Column(Text)
    decision = Column(String(50))  # ship, dont_ship, continue, redesign
    decision_rationale = Column(Text)
    
    # Implementation details
    feature_flags = Column(JSON, nullable=False, default={})  # Feature flags used
    config_overrides = Column(JSON, nullable=False, default={})  # Config overrides per variant
    
    # Quality and monitoring
    data_quality_score = Column(Float, nullable=False, default=1.0)
    monitoring_alerts = Column(JSON, nullable=False, default=[])
    issues_encountered = Column(JSON, nullable=False, default=[])
    
    # Relationships
    tenant = relationship("Tenant", back_populates="experiments")
    answers = relationship("Answer", back_populates="experiment")
    
    # Indexes
    __table_args__ = (
        Index('idx_experiment_tenant_status', 'tenant_id', 'status'),
        Index('idx_experiment_dates', 'started_at', 'actual_end_at'),
        Index('idx_experiment_type_status', 'experiment_type', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<Experiment(name={self.name}, status={self.status}, participants={self.total_participants})>"
    
    @property
    def is_active(self) -> bool:
        """Check if experiment is currently active."""
        return self.status == ExperimentStatus.ACTIVE.value
    
    @property
    def is_completed(self) -> bool:
        """Check if experiment is completed."""
        return self.status == ExperimentStatus.COMPLETED.value
    
    @property
    def has_sufficient_sample(self) -> bool:
        """Check if experiment has sufficient sample size."""
        return self.total_participants >= self.minimum_sample_size
    
    @property
    def duration_actual_days(self) -> Optional[float]:
        """Calculate actual duration in days."""
        if not self.started_at:
            return None
        
        from datetime import datetime
        
        try:
            start = datetime.fromisoformat(self.started_at.replace('Z', '+00:00'))
            
            if self.actual_end_at:
                end = datetime.fromisoformat(self.actual_end_at.replace('Z', '+00:00'))
            else:
                end = datetime.utcnow().replace(tzinfo=start.tzinfo)
            
            delta = end - start
            return delta.total_seconds() / (24 * 3600)  # Convert to days
        except:
            return None
    
    def get_variant_allocation(self, variant: str) -> float:
        """Get traffic allocation for a variant."""
        if not self.variant_weights:
            # Equal allocation if no weights specified
            return 1.0 / len(self.variants) if self.variants else 0.0
        
        return self.variant_weights.get(variant, 0.0)
    
    def assign_variant(self, user_id: str) -> str:
        """Assign a variant to a user based on consistent hashing."""
        import hashlib
        
        if not self.variants:
            return "control"
        
        # Create consistent hash
        hash_input = f"{self.id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Normalize to 0-1
        normalized = (hash_value % 1000000) / 1000000.0
        
        # Apply traffic allocation
        if normalized > self.traffic_allocation:
            return None  # User not in experiment
        
        # Assign variant based on weights
        cumulative_weight = 0.0
        adjusted_random = normalized / self.traffic_allocation  # Rescale to 0-1 for participants
        
        for variant in self.variants:
            if isinstance(variant, dict):
                variant_name = variant.get("name", "control")
            else:
                variant_name = variant
            
            weight = self.get_variant_allocation(variant_name)
            cumulative_weight += weight
            
            if adjusted_random <= cumulative_weight:
                return variant_name
        
        # Fallback to first variant
        return self.variants[0] if self.variants else "control"
    
    def record_participant(self, variant: str, user_id: str = None):
        """Record a new participant in the experiment."""
        self.total_participants += 1
        
        if not self.participants_per_variant:
            self.participants_per_variant = {}
        
        current_count = self.participants_per_variant.get(variant, 0)
        self.participants_per_variant[variant] = current_count + 1
    
    def start_experiment(self):
        """Start the experiment."""
        from datetime import datetime, timedelta
        
        if self.status != ExperimentStatus.DRAFT.value:
            raise ValueError(f"Cannot start experiment in status: {self.status}")
        
        now = datetime.utcnow()
        self.status = ExperimentStatus.ACTIVE.value
        self.started_at = now.isoformat() + "Z"
        
        # Set planned end date
        if self.duration_days:
            planned_end = now + timedelta(days=self.duration_days)
            self.planned_end_at = planned_end.isoformat() + "Z"
    
    def pause_experiment(self, reason: str = None):
        """Pause the experiment."""
        if self.status != ExperimentStatus.ACTIVE.value:
            raise ValueError(f"Cannot pause experiment in status: {self.status}")
        
        self.status = ExperimentStatus.PAUSED.value
        
        if reason:
            if not self.analysis_notes:
                self.analysis_notes = reason
            else:
                self.analysis_notes += f"\n\nPaused: {reason}"
    
    def complete_experiment(self, decision: str = None, rationale: str = None):
        """Complete the experiment."""
        from datetime import datetime
        
        if self.status not in [ExperimentStatus.ACTIVE.value, ExperimentStatus.PAUSED.value]:
            raise ValueError(f"Cannot complete experiment in status: {self.status}")
        
        self.status = ExperimentStatus.COMPLETED.value
        self.actual_end_at = datetime.utcnow().isoformat() + "Z"
        
        if decision:
            self.decision = decision
        
        if rationale:
            self.decision_rationale = rationale
    
    def update_results(self, metric: str, variant_results: Dict[str, float], 
                      is_significant: bool = False, confidence_interval: Dict = None):
        """Update experiment results."""
        from datetime import datetime
        
        if not self.results:
            self.results = {}
        
        self.results[metric] = variant_results
        self.is_significant = is_significant
        
        if confidence_interval:
            if not self.confidence_interval:
                self.confidence_interval = {}
            self.confidence_interval[metric] = confidence_interval
        
        # Determine winning variant for primary metric
        if metric == self.primary_metric and variant_results:
            self.winning_variant = max(variant_results.keys(), key=lambda k: variant_results[k])
        
        self.analyzed_at = datetime.utcnow().isoformat() + "Z"
    
    def get_variant_config(self, variant: str) -> Dict:
        """Get configuration for a specific variant."""
        base_config = self.config_overrides.get("base", {})
        variant_config = self.config_overrides.get(variant, {})
        
        # Merge base config with variant-specific overrides
        config = base_config.copy()
        config.update(variant_config)
        
        return config
    
    def check_early_stopping(self) -> bool:
        """Check if experiment should be stopped early."""
        # Check for sufficient statistical power
        if not self.has_sufficient_sample:
            return False
        
        # Check if we have significant results
        if not self.is_significant:
            return False
        
        # Check if effect size is above minimum
        if self.primary_metric in self.results:
            results = self.results[self.primary_metric]
            if len(results) >= 2:
                values = list(results.values())
                effect_size = abs(max(values) - min(values)) / min(values)
                return effect_size >= self.minimum_effect_size
        
        return False
    
    def calculate_sample_size_needed(self, effect_size: float = None, 
                                   power: float = None, alpha: float = None) -> int:
        """Calculate required sample size for statistical significance."""
        # This is a simplified calculation - in production you'd use proper statistical libraries
        import math
        
        effect = effect_size or self.minimum_effect_size
        pow = power or self.power
        sig = alpha or self.significance_level
        
        # Simplified formula for two-sample test
        # In practice, use statsmodels or similar
        z_alpha = 1.96  # For alpha = 0.05
        z_beta = 0.84   # For power = 0.8
        
        n_per_group = 2 * ((z_alpha + z_beta) / effect) ** 2
        
        # Total sample size (assuming 2 variants)
        total_needed = int(n_per_group * 2)
        
        return max(total_needed, self.minimum_sample_size)