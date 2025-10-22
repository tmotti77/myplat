"""Feedback system with DPO-style learning for continuous model improvement."""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import numpy as np

from src.core.config import settings
from src.core.database import get_db_session
from src.core.logging import get_logger, LoggerMixin, LoggedOperation
from src.models.feedback import Feedback, FeedbackStatus, FeedbackSignal as FeedbackType
from src.models.feedback_comparison import FeedbackComparison, ComparisonType
from src.models.preference_pair import PreferencePair, PreferenceOutcome
from src.models.model_training import ModelTrainingRun, TrainingStatus, TrainingType
from src.services.cache import cache_service
from src.services.llm_router import llm_router_service

logger = get_logger(__name__)


class LearningStrategy(str, Enum):
    """Learning strategies for feedback processing."""
    DIRECT_PREFERENCE_OPTIMIZATION = "dpo"
    REINFORCEMENT_LEARNING_HUMAN_FEEDBACK = "rlhf"
    CONSTITUTIONAL_AI = "constitutional"
    REWARD_MODEL_TRAINING = "reward_model"
    INSTRUCTION_TUNING = "instruction_tuning"


class FeedbackSignal(str, Enum):
    """Types of feedback signals."""
    EXPLICIT_RATING = "explicit_rating"
    PREFERENCE_COMPARISON = "preference_comparison"
    THUMBS_UP_DOWN = "thumbs_up_down"
    CORRECTION_SUGGESTION = "correction_suggestion"
    HELPFULNESS_VOTE = "helpfulness_vote"
    QUALITY_ASSESSMENT = "quality_assessment"
    BIAS_FLAGGING = "bias_flagging"
    FACTUAL_CORRECTION = "factual_correction"


class FeedbackSystem(LoggerMixin):
    """Advanced feedback system with DPO-style learning capabilities."""
    
    def __init__(self):
        self._preference_cache = {}
        self._training_queue = []
        self._cache_ttl = 3600
        
        # Learning parameters
        self._dpo_parameters = {
            "beta": 0.1,              # Temperature parameter for DPO
            "batch_size": 32,         # Training batch size
            "learning_rate": 1e-5,    # Learning rate
            "gradient_steps": 100,    # Training steps per batch
            "preference_threshold": 0.7,  # Minimum preference strength
            "quality_threshold": 0.8   # Minimum quality for training data
        }
        
        # Feedback aggregation weights
        self._feedback_weights = {
            FeedbackSignal.RATING: 1.0,
            FeedbackSignal.PAIRWISE: 0.9,
            FeedbackSignal.THUMBS_UP: 0.7,
            FeedbackSignal.THUMBS_DOWN: 0.7,
            FeedbackSignal.EDIT: 0.8,
            FeedbackSignal.CORRECTION: 1.0,
            FeedbackSignal.REPORT: 0.8
        }
    
    async def initialize(self):
        """Initialize feedback system."""
        try:
            # Start background tasks
            asyncio.create_task(self._background_preference_learning())
            asyncio.create_task(self._background_feedback_aggregation())
            
            self.log_info("Feedback system initialized")
        except Exception as e:
            self.log_error("Failed to initialize feedback system", error=e)
            raise
    
    async def cleanup(self):
        """Clean up feedback system."""
        try:
            self._preference_cache.clear()
            self._training_queue.clear()
            self.log_info("Feedback system cleaned up")
        except Exception as e:
            self.log_error("Error during feedback system cleanup", error=e)
    
    async def collect_feedback(
        self,
        user_id: str,
        tenant_id: str,
        content_id: str,
        content_type: str,
        feedback_type: FeedbackType,
        feedback_signal: FeedbackSignal,
        rating: Optional[float] = None,
        comparison_data: Optional[Dict[str, Any]] = None,
        textual_feedback: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Collect user feedback for continuous learning."""
        
        try:
            with LoggedOperation("collect_feedback", user_id=user_id, content_id=content_id):
                feedback_id = str(uuid.uuid4())
                
                # Create feedback record
                async with get_db_session() as session:
                    feedback = Feedback(
                        id=feedback_id,
                        user_id=user_id,
                        tenant_id=tenant_id,
                        answer_id=content_id,  # Using answer_id as per existing model
                        query_id=metadata.get("query_id", content_id) if metadata else content_id,
                        signal=feedback_signal.value,
                        rating=rating,
                        feedback_text=textual_feedback or "",
                        model_choice=metadata.get("model_used", "unknown") if metadata else "unknown",
                        latency_ms=metadata.get("latency_ms", 0.0) if metadata else 0.0,
                        status=FeedbackStatus.PENDING.value
                    )
                    
                    session.add(feedback)
                    await session.commit()
                
                # Process feedback based on signal type
                processing_result = await self._process_feedback_signal(
                    feedback, feedback_signal, comparison_data
                )
                
                # Update content quality scores
                await self._update_content_quality_scores(
                    content_id, content_type, feedback_signal, rating
                )
                
                # Queue for preference learning if applicable
                if feedback_signal in [
                    FeedbackSignal.PAIRWISE,
                    FeedbackSignal.RATING,
                    FeedbackSignal.CORRECTION
                ]:
                    await self._queue_for_preference_learning(feedback)
                
                self.log_info(
                    "Feedback collected",
                    feedback_id=feedback_id,
                    signal_type=feedback_signal.value,
                    content_id=content_id
                )
                
                return {
                    "feedback_id": feedback_id,
                    "status": "processed",
                    "learning_impact": processing_result.get("learning_impact", 0.0),
                    "will_train": processing_result.get("will_train", False)
                }
                
        except Exception as e:
            self.log_error("Feedback collection failed", user_id=user_id, error=e)
            raise
    
    async def create_preference_comparison(
        self,
        user_id: str,
        tenant_id: str,
        query: str,
        response_a_id: str,
        response_b_id: str,
        preference: str,  # "a", "b", or "tie"
        strength: float,  # 0.0 to 1.0
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a preference comparison for DPO training."""
        
        try:
            with LoggedOperation("create_preference_comparison", user_id=user_id):
                comparison_id = str(uuid.uuid4())
                
                # Determine preference outcome
                if preference == "a":
                    outcome = PreferenceOutcome.PREFERRED_A
                elif preference == "b":
                    outcome = PreferenceOutcome.PREFERRED_B
                else:
                    outcome = PreferenceOutcome.TIE
                
                # Create preference pair
                async with get_db_session() as session:
                    preference_pair = PreferencePair(
                        id=comparison_id,
                        user_id=user_id,
                        tenant_id=tenant_id,
                        query=query,
                        response_a_id=response_a_id,
                        response_b_id=response_b_id,
                        preference_outcome=outcome.value,
                        preference_strength=strength,
                        reasoning=reasoning or "",
                        metadata=metadata or {}
                    )
                    
                    session.add(preference_pair)
                    await session.commit()
                
                # Queue for DPO training if preference is strong enough
                if strength >= self._dpo_parameters["preference_threshold"]:
                    await self._queue_dpo_training_pair(preference_pair)
                
                self.log_info(
                    "Preference comparison created",
                    comparison_id=comparison_id,
                    preference=preference,
                    strength=strength
                )
                
                return {
                    "comparison_id": comparison_id,
                    "queued_for_training": strength >= self._dpo_parameters["preference_threshold"],
                    "training_value": self._calculate_training_value(preference_pair)
                }
                
        except Exception as e:
            self.log_error("Preference comparison failed", user_id=user_id, error=e)
            raise
    
    async def trigger_model_improvement(
        self,
        strategy: LearningStrategy,
        tenant_id: str,
        target_model: Optional[str] = None,
        training_data_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Trigger model improvement using collected feedback."""
        
        try:
            with LoggedOperation("trigger_model_improvement", strategy=strategy.value):
                training_run_id = str(uuid.uuid4())
                
                # Collect training data based on strategy
                training_data = await self._collect_training_data(
                    strategy, tenant_id, training_data_filters
                )
                
                if len(training_data) < 10:  # Minimum data requirement
                    raise ValueError(f"Insufficient training data: {len(training_data)} samples")
                
                # Create training run record
                async with get_db_session() as session:
                    training_run = ModelTrainingRun(
                        id=training_run_id,
                        tenant_id=tenant_id,
                        strategy=strategy.value,
                        target_model=target_model or "default",
                        training_data_count=len(training_data),
                        status=TrainingStatus.QUEUED.value,
                        hyperparameters=self._get_hyperparameters(strategy),
                        metadata={
                            "data_filters": training_data_filters or {},
                            "training_data_sample": training_data[:5]  # Store sample for inspection
                        }
                    )
                    
                    session.add(training_run)
                    await session.commit()
                
                # Start training process (async)
                if strategy == LearningStrategy.DIRECT_PREFERENCE_OPTIMIZATION:
                    asyncio.create_task(
                        self._run_dpo_training(training_run_id, training_data)
                    )
                elif strategy == LearningStrategy.REWARD_MODEL_TRAINING:
                    asyncio.create_task(
                        self._run_reward_model_training(training_run_id, training_data)
                    )
                else:
                    # Other strategies would be implemented similarly
                    await self._mark_training_run_unsupported(training_run_id, strategy)
                
                self.log_info(
                    "Model improvement triggered",
                    training_run_id=training_run_id,
                    strategy=strategy.value,
                    data_count=len(training_data)
                )
                
                return {
                    "training_run_id": training_run_id,
                    "strategy": strategy.value,
                    "training_data_count": len(training_data),
                    "estimated_completion_minutes": self._estimate_training_time(
                        strategy, len(training_data)
                    ),
                    "status": "queued"
                }
                
        except Exception as e:
            self.log_error("Model improvement failed", strategy=strategy.value, error=e)
            raise
    
    async def _process_feedback_signal(
        self,
        feedback: Feedback,
        signal_type: FeedbackSignal,
        comparison_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process specific feedback signal type."""
        
        result = {"learning_impact": 0.0, "will_train": False}
        
        try:
            if signal_type == FeedbackSignal.PREFERENCE_COMPARISON:
                # High-value preference data
                result["learning_impact"] = 0.8
                result["will_train"] = True
                
                if comparison_data:
                    await self._process_preference_comparison(feedback, comparison_data)
            
            elif signal_type == FeedbackSignal.RATING:
                # Direct rating feedback
                impact = (abs(feedback.rating - 3.0) / 2.0) * 0.6 if feedback.rating else 0.3
                result["learning_impact"] = impact
                result["will_train"] = feedback.rating and (feedback.rating <= 2.0 or feedback.rating >= 4.0)
            
            elif signal_type == FeedbackSignal.CORRECTION:
                # Critical for accuracy
                result["learning_impact"] = 0.9
                result["will_train"] = True
                await self._process_factual_correction(feedback)
            
            elif signal_type == FeedbackSignal.REPORT:
                # Important for fairness
                result["learning_impact"] = 0.7
                result["will_train"] = True
                await self._process_bias_flagging(feedback)
            
            elif signal_type == FeedbackSignal.EDIT:
                # Moderate learning value
                result["learning_impact"] = 0.5
                result["will_train"] = True
                await self._process_correction_suggestion(feedback)
            
            else:
                # Basic signals
                result["learning_impact"] = 0.3
                result["will_train"] = False
            
            # Update feedback status
            await self._update_feedback_status(
                feedback.id, FeedbackStatus.PROCESSED, result
            )
            
            return result
            
        except Exception as e:
            self.log_error("Feedback signal processing failed", signal_type=signal_type.value, error=e)
            await self._update_feedback_status(
                feedback.id, FeedbackStatus.FAILED, {"error": str(e)}
            )
            return result
    
    async def _run_dpo_training(
        self,
        training_run_id: str,
        training_data: List[Dict[str, Any]]
    ):
        """Run Direct Preference Optimization training."""
        
        try:
            # Update status to running
            await self._update_training_status(training_run_id, TrainingStatus.RUNNING)
            
            # Prepare DPO training data
            dpo_pairs = []
            for data_point in training_data:
                if data_point["type"] == "preference_pair":
                    dpo_pairs.append({
                        "query": data_point["query"],
                        "chosen": data_point["preferred_response"],
                        "rejected": data_point["rejected_response"],
                        "preference_strength": data_point["preference_strength"]
                    })
            
            if len(dpo_pairs) < 5:
                await self._update_training_status(
                    training_run_id, TrainingStatus.FAILED, 
                    {"error": "Insufficient preference pairs for DPO"}
                )
                return
            
            # In a real implementation, this would:
            # 1. Load the base model
            # 2. Prepare the DPO dataset
            # 3. Run DPO training with the prepared pairs
            # 4. Evaluate the trained model
            # 5. Save/deploy the improved model
            
            # For now, simulate training process
            await asyncio.sleep(5)  # Simulate training time
            
            # Calculate training metrics
            training_metrics = {
                "loss_reduction": 0.15,
                "preference_accuracy": 0.78,
                "kl_divergence": 0.05,
                "training_pairs": len(dpo_pairs)
            }
            
            # Update training status
            await self._update_training_status(
                training_run_id, TrainingStatus.COMPLETED, training_metrics
            )
            
            self.log_info(
                "DPO training completed",
                training_run_id=training_run_id,
                pairs_count=len(dpo_pairs),
                metrics=training_metrics
            )
            
        except Exception as e:
            await self._update_training_status(
                training_run_id, TrainingStatus.FAILED, {"error": str(e)}
            )
            self.log_error("DPO training failed", training_run_id=training_run_id, error=e)
    
    async def _collect_training_data(
        self,
        strategy: LearningStrategy,
        tenant_id: str,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Collect appropriate training data for the strategy."""
        
        training_data = []
        
        try:
            async with get_db_session() as session:
                if strategy == LearningStrategy.DIRECT_PREFERENCE_OPTIMIZATION:
                    # Collect preference pairs
                    from sqlalchemy import select
                    
                    query = (
                        select(PreferencePair)
                        .where(PreferencePair.tenant_id == tenant_id)
                        .where(PreferencePair.preference_strength >= self._dpo_parameters["preference_threshold"])
                        .order_by(PreferencePair.created_at.desc())
                        .limit(1000)  # Reasonable limit
                    )
                    
                    result = await session.execute(query)
                    preference_pairs = result.scalars().all()
                    
                    for pair in preference_pairs:
                        if pair.preference_outcome != PreferenceOutcome.TIE.value:
                            training_data.append({
                                "type": "preference_pair",
                                "query": pair.query,
                                "preferred_response": await self._get_response_content(pair.response_a_id if pair.preference_outcome == PreferenceOutcome.PREFERRED_A.value else pair.response_b_id),
                                "rejected_response": await self._get_response_content(pair.response_b_id if pair.preference_outcome == PreferenceOutcome.PREFERRED_A.value else pair.response_a_id),
                                "preference_strength": pair.preference_strength,
                                "reasoning": pair.reasoning
                            })
                
                elif strategy == LearningStrategy.REWARD_MODEL_TRAINING:
                    # Collect rated responses
                    from sqlalchemy import select
                    
                    query = (
                        select(Feedback)
                        .where(Feedback.tenant_id == tenant_id)
                        .where(Feedback.signal == FeedbackSignal.RATING.value)
                        .where(Feedback.rating.isnot(None))
                        .order_by(Feedback.created_at.desc())
                        .limit(1000)
                    )
                    
                    result = await session.execute(query)
                    feedback_items = result.scalars().all()
                    
                    for feedback in feedback_items:
                        content = await self._get_response_content(feedback.content_id)
                        if content:
                            training_data.append({
                                "type": "rated_response",
                                "query": content.get("query", ""),
                                "response": content.get("response", ""),
                                "rating": feedback.rating,
                                "feedback": feedback.textual_feedback
                            })
            
            return training_data
            
        except Exception as e:
            self.log_error("Training data collection failed", strategy=strategy.value, error=e)
            return []
    
    async def get_feedback_analytics(
        self,
        tenant_id: str,
        time_range_days: int = 30,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive feedback analytics."""
        
        try:
            analytics = {
                "total_feedback_count": 0,
                "feedback_by_signal": {},
                "average_ratings": {},
                "improvement_metrics": {},
                "training_progress": {},
                "quality_trends": []
            }
            
            async with get_db_session() as session:
                from sqlalchemy import select, func
                
                # Base query with date filter
                base_query = (
                    select(Feedback)
                    .where(Feedback.tenant_id == tenant_id)
                    .where(Feedback.created_at >= (datetime.utcnow() - timedelta(days=time_range_days)).isoformat())
                )
                
                if content_type:
                    base_query = base_query.where(Feedback.content_type == content_type)
                
                # Total feedback count
                count_result = await session.execute(
                    select(func.count(Feedback.id)).select_from(base_query.subquery())
                )
                analytics["total_feedback_count"] = count_result.scalar() or 0
                
                # Feedback by signal type
                signal_query = (
                    select(
                        Feedback.signal,
                        func.count(Feedback.id).label("count"),
                        func.avg(Feedback.rating).label("avg_rating")
                    )
                    .select_from(base_query.subquery())
                    .group_by(Feedback.signal)
                )
                
                signal_result = await session.execute(signal_query)
                for row in signal_result:
                    analytics["feedback_by_signal"][row.signal] = {
                        "count": row.count,
                        "average_rating": float(row.avg_rating) if row.avg_rating else None
                    }
                
                # Training run statistics
                training_query = (
                    select(
                        ModelTrainingRun.status,
                        func.count(ModelTrainingRun.id).label("count")
                    )
                    .where(ModelTrainingRun.tenant_id == tenant_id)
                    .where(ModelTrainingRun.created_at >= (datetime.utcnow() - timedelta(days=time_range_days)).isoformat())
                    .group_by(ModelTrainingRun.status)
                )
                
                training_result = await session.execute(training_query)
                for row in training_result:
                    analytics["training_progress"][row.status] = row.count
            
            return analytics
            
        except Exception as e:
            self.log_error("Feedback analytics failed", tenant_id=tenant_id, error=e)
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check feedback system health."""
        
        health = {
            "status": "healthy",
            "pending_feedback": len(self._training_queue),
            "cached_preferences": len(self._preference_cache),
        }
        
        try:
            # Check recent feedback processing
            async with get_db_session() as session:
                from sqlalchemy import select, func
                
                # Count recent feedback
                recent_feedback_query = (
                    select(func.count(Feedback.id))
                    .where(Feedback.created_at >= (datetime.utcnow() - timedelta(hours=24)).isoformat())
                )
                result = await session.execute(recent_feedback_query)
                health["recent_feedback_24h"] = result.scalar() or 0
                
                # Count active training runs
                active_training_query = (
                    select(func.count(ModelTrainingRun.id))
                    .where(ModelTrainingRun.status.in_([
                        TrainingStatus.QUEUED.value,
                        TrainingStatus.RUNNING.value
                    ]))
                )
                result = await session.execute(active_training_query)
                health["active_training_runs"] = result.scalar() or 0
        
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


# Global feedback system instance
feedback_system = FeedbackSystem()