"""Model training tracking for continuous improvement."""
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, JSON

from src.models.base import BaseModel


class TrainingStatus(str, Enum):
    """Training run status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TrainingType(str, Enum):
    """Types of training runs."""
    DPO = "dpo"                    # Direct Preference Optimization
    RLHF = "rlhf"                  # Reinforcement Learning from Human Feedback
    REWARD_MODEL = "reward_model"   # Reward model training
    INSTRUCTION_TUNING = "instruction_tuning"
    CONSTITUTIONAL = "constitutional"
    FINE_TUNING = "fine_tuning"


class ModelTrainingRun(BaseModel):
    """Model for tracking training runs and experiments."""
    
    __tablename__ = "model_training_runs"
    
    # Core identification
    tenant_id = Column(String, nullable=False, index=True)
    
    # Training details
    strategy = Column(String, nullable=False, index=True)
    training_type = Column(String, nullable=True)
    target_model = Column(String, nullable=False)
    base_model = Column(String, nullable=True)
    
    # Status tracking
    status = Column(String, default=TrainingStatus.QUEUED.value, index=True)
    progress_percentage = Column(Float, default=0.0)
    
    # Data and configuration
    training_data_count = Column(Integer, default=0)
    validation_data_count = Column(Integer, default=0)
    hyperparameters = Column(JSON, default={})
    
    # Timing
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    
    # Results and metrics
    final_metrics = Column(JSON, default={})
    validation_metrics = Column(JSON, default={})
    
    # Model outputs
    model_checkpoint_path = Column(String, nullable=True)
    model_artifacts = Column(JSON, default={})
    
    # Error handling
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Resource usage
    compute_cost_usd = Column(Float, default=0.0)
    gpu_hours_used = Column(Float, default=0.0)
    
    # Evaluation
    evaluation_results = Column(JSON, default={})
    human_eval_score = Column(Float, nullable=True)
    automated_eval_score = Column(Float, nullable=True)
    
    # Deployment
    deployed = Column(String, default="false")  # Boolean as string
    deployment_target = Column(String, nullable=True)
    deployed_at = Column(String, nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON, default={})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def start_training(self):
        """Mark training as started."""
        from datetime import datetime
        
        self.status = TrainingStatus.RUNNING.value
        self.started_at = datetime.utcnow().isoformat() + "Z"
        self.progress_percentage = 0.0
    
    def complete_training(self, metrics: dict):
        """Mark training as completed."""
        from datetime import datetime
        
        self.status = TrainingStatus.COMPLETED.value
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        self.progress_percentage = 100.0
        self.final_metrics = metrics
        
        # Calculate duration if started
        if self.started_at:
            start_time = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            end_time = datetime.utcnow().replace(tzinfo=start_time.tzinfo)
            duration = end_time - start_time
            self.duration_minutes = duration.total_seconds() / 60
    
    def fail_training(self, error_message: str):
        """Mark training as failed."""
        from datetime import datetime
        
        self.status = TrainingStatus.FAILED.value
        self.error_message = error_message
        self.completed_at = datetime.utcnow().isoformat() + "Z"
        
        # Calculate duration if started
        if self.started_at:
            start_time = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
            end_time = datetime.utcnow().replace(tzinfo=start_time.tzinfo)
            duration = end_time - start_time
            self.duration_minutes = duration.total_seconds() / 60
    
    def update_progress(self, percentage: float, current_metrics: dict = None):
        """Update training progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        if current_metrics:
            if not self.extra_metadata:
                self.extra_metadata = {}
            self.extra_metadata["current_metrics"] = current_metrics
    
    def deploy_model(self, target: str):
        """Mark model as deployed."""
        from datetime import datetime
        
        self.deployed = "true"
        self.deployment_target = target
        self.deployed_at = datetime.utcnow().isoformat() + "Z"
    
    @property
    def is_completed(self) -> bool:
        """Check if training is completed."""
        return self.status == TrainingStatus.COMPLETED.value
    
    @property
    def is_running(self) -> bool:
        """Check if training is running."""
        return self.status == TrainingStatus.RUNNING.value
    
    @property
    def is_deployed(self) -> bool:
        """Check if model is deployed."""
        return self.deployed == "true"
    
    def get_training_efficiency(self) -> float:
        """Calculate training efficiency score."""
        if not self.is_completed or not self.duration_minutes:
            return 0.0
        
        # Simple efficiency metric based on data/time ratio
        if self.training_data_count > 0 and self.duration_minutes > 0:
            return min(1.0, self.training_data_count / (self.duration_minutes * 10))
        
        return 0.0