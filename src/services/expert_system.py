"""Expert reputation system with community features and quality scoring."""
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import numpy as np

from src.core.config import settings
from src.core.database import get_db_session
from src.core.logging import get_logger, LoggerMixin, LoggedOperation
from src.models.expert import Expert, ExpertStatus
from src.models.reputation import Reputation, ReputationEvent, ReputationEventType
from src.models.badge import Badge, BadgeType, UserBadge
from src.models.peer_review import PeerReview, ReviewStatus, ReviewType
from src.models.contribution import Contribution, ContributionType, ContributionStatus
from src.services.cache import cache_service

logger = get_logger(__name__)


class ReputationCalculationMode(str, Enum):
    """Reputation calculation modes."""
    BASIC = "basic"              # Simple scoring
    WEIGHTED = "weighted"        # Weight by content quality
    PEER_REVIEWED = "peer_reviewed"  # Include peer review scores
    DOMAIN_SPECIFIC = "domain_specific"  # Domain expertise weighting
    TIME_DECAY = "time_decay"    # Apply time-based decay


class ExpertSystemEngine(LoggerMixin):
    """Expert reputation system for community knowledge quality."""
    
    def __init__(self):
        self._reputation_cache = {}
        self._expert_cache = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Reputation scoring weights
        self._scoring_weights = {
            "content_quality": 0.30,
            "peer_reviews": 0.25,
            "user_feedback": 0.20,
            "consistency": 0.15,
            "domain_expertise": 0.10
        }
        
        # Badge requirements
        self._badge_requirements = {
            BadgeType.CONTRIBUTOR: {"contributions": 10, "avg_rating": 3.0},
            BadgeType.EXPERT: {"contributions": 50, "avg_rating": 4.0, "peer_reviews": 10},
            BadgeType.MASTER: {"contributions": 200, "avg_rating": 4.5, "peer_reviews": 50},
            BadgeType.PIONEER: {"contributions": 500, "avg_rating": 4.7, "peer_reviews": 100},
            BadgeType.QUALITY_CHAMPION: {"quality_score": 0.9, "contributions": 25},
            BadgeType.PEER_REVIEWER: {"reviews_given": 20, "review_accuracy": 0.8},
            BadgeType.DOMAIN_EXPERT: {"domain_contributions": 30, "domain_rating": 4.5},
            BadgeType.MENTOR: {"mentorship_score": 0.8, "helped_users": 10},
            BadgeType.INNOVATOR: {"novel_contributions": 5, "innovation_score": 0.9},
            BadgeType.TRUSTED: {"trust_score": 0.95, "contributions": 100}
        }
    
    async def initialize(self):
        """Initialize expert system."""
        try:
            self.log_info("Expert system initialized")
        except Exception as e:
            self.log_error("Failed to initialize expert system", error=e)
            raise
    
    async def cleanup(self):
        """Clean up expert system."""
        try:
            self._reputation_cache.clear()
            self._expert_cache.clear()
            self.log_info("Expert system cleaned up")
        except Exception as e:
            self.log_error("Error during expert system cleanup", error=e)
    
    async def register_expert(
        self,
        user_id: str,
        tenant_id: str,
        expertise_areas: List[str],
        credentials: Optional[Dict[str, Any]] = None,
        verification_documents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Register a user as an expert in specific domains."""
        
        try:
            with LoggedOperation("register_expert", user_id=user_id):
                async with get_db_session() as session:
                    # Check if expert already exists
                    from sqlalchemy import select
                    
                    existing_query = select(Expert).where(
                        Expert.user_id == user_id,
                        Expert.tenant_id == tenant_id
                    )
                    result = await session.execute(existing_query)
                    existing_expert = result.scalar_one_or_none()
                    
                    if existing_expert:
                        # Update existing expert
                        expert = existing_expert
                        expert.expertise_areas = expertise_areas
                        expert.credentials = credentials or {}
                        expert.verification_documents = verification_documents or []
                        expert.updated_at = datetime.utcnow().isoformat() + "Z"
                    else:
                        # Create new expert
                        expert = Expert(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            tenant_id=tenant_id,
                            expertise_areas=expertise_areas,
                            status=ExpertStatus.PENDING.value,
                            credentials=credentials or {},
                            verification_documents=verification_documents or []
                        )
                        session.add(expert)
                    
                    await session.commit()
                    
                    # Create initial reputation record
                    await self._create_initial_reputation(user_id, tenant_id, session)
                    
                    self.log_info(
                        "Expert registered",
                        user_id=user_id,
                        expertise_areas=expertise_areas,
                        status=expert.status
                    )
                    
                    return {
                        "expert_id": expert.id,
                        "status": expert.status,
                        "expertise_areas": expert.expertise_areas,
                        "pending_verification": expert.status == ExpertStatus.PENDING.value
                    }
                    
        except Exception as e:
            self.log_error("Expert registration failed", user_id=user_id, error=e)
            raise
    
    async def calculate_reputation_score(
        self,
        user_id: str,
        tenant_id: str,
        mode: ReputationCalculationMode = ReputationCalculationMode.WEIGHTED,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive reputation score for a user."""
        
        try:
            # Check cache first
            cache_key = f"reputation:{user_id}:{mode.value}:{domain or 'global'}"
            cached_score = await cache_service.get(cache_key)
            if cached_score:
                return cached_score
            
            with LoggedOperation("calculate_reputation", user_id=user_id):
                start_time = time.time()
                
                # Get user's contributions
                contributions = await self._get_user_contributions(user_id, tenant_id, domain)
                
                # Get peer review data
                peer_reviews = await self._get_peer_review_data(user_id, tenant_id, domain)
                
                # Get user feedback data
                user_feedback = await self._get_user_feedback_data(user_id, tenant_id, domain)
                
                # Calculate component scores
                content_quality_score = await self._calculate_content_quality_score(contributions)
                peer_review_score = await self._calculate_peer_review_score(peer_reviews)
                user_feedback_score = await self._calculate_user_feedback_score(user_feedback)
                consistency_score = await self._calculate_consistency_score(contributions)
                domain_expertise_score = await self._calculate_domain_expertise_score(
                    user_id, tenant_id, domain, contributions
                )
                
                # Apply time decay if requested
                if mode == ReputationCalculationMode.TIME_DECAY:
                    decay_factor = await self._calculate_time_decay_factor(contributions)
                    content_quality_score *= decay_factor
                    peer_review_score *= decay_factor
                    user_feedback_score *= decay_factor
                
                # Calculate weighted final score
                component_scores = {
                    "content_quality": content_quality_score,
                    "peer_reviews": peer_review_score,
                    "user_feedback": user_feedback_score,
                    "consistency": consistency_score,
                    "domain_expertise": domain_expertise_score
                }
                
                # Adjust weights based on mode
                weights = self._get_adjusted_weights(mode, component_scores)
                
                final_score = sum(
                    score * weights[component]
                    for component, score in component_scores.items()
                )
                
                # Normalize to 0-100 scale
                final_score = max(0, min(100, final_score * 100))
                
                # Calculate confidence level
                confidence = await self._calculate_score_confidence(
                    contributions, peer_reviews, user_feedback
                )
                
                # Determine reputation level
                reputation_level = self._get_reputation_level(final_score)
                
                reputation_data = {
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "domain": domain,
                    "overall_score": round(final_score, 2),
                    "reputation_level": reputation_level,
                    "confidence": round(confidence, 3),
                    "component_scores": {
                        k: round(v * 100, 2) for k, v in component_scores.items()
                    },
                    "weights_used": weights,
                    "calculation_mode": mode.value,
                    "data_points": {
                        "contributions": len(contributions),
                        "peer_reviews_received": len([r for r in peer_reviews if r.get("type") == "received"]),
                        "peer_reviews_given": len([r for r in peer_reviews if r.get("type") == "given"]),
                        "user_feedback_count": len(user_feedback)
                    },
                    "calculated_at": datetime.utcnow().isoformat() + "Z",
                    "calculation_time_ms": round((time.time() - start_time) * 1000, 2)
                }
                
                # Store in database
                await self._store_reputation_calculation(reputation_data)
                
                # Cache result
                await cache_service.set(cache_key, reputation_data, ttl=self._cache_ttl)
                
                return reputation_data
                
        except Exception as e:
            self.log_error("Reputation calculation failed", user_id=user_id, error=e)
            raise
    
    async def submit_peer_review(
        self,
        reviewer_id: str,
        content_id: str,
        content_type: str,
        tenant_id: str,
        review_type: ReviewType,
        scores: Dict[str, float],
        comments: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit a peer review for content."""
        
        try:
            with LoggedOperation("submit_peer_review", reviewer_id=reviewer_id):
                # Validate reviewer eligibility
                is_eligible = await self._check_reviewer_eligibility(
                    reviewer_id, tenant_id, content_type
                )
                
                if not is_eligible:
                    raise ValueError("Reviewer not eligible for this content type")
                
                # Create peer review
                async with get_db_session() as session:
                    review = PeerReview(
                        id=str(uuid.uuid4()),
                        reviewer_id=reviewer_id,
                        content_id=content_id,
                        content_type=content_type,
                        tenant_id=tenant_id,
                        review_type=review_type.value,
                        scores=scores,
                        comments=comments or "",
                        status=ReviewStatus.SUBMITTED.value,
                        metadata=metadata or {}
                    )
                    
                    session.add(review)
                    await session.commit()
                    
                    # Update reviewer's reputation for contributing reviews
                    await self._record_reputation_event(
                        user_id=reviewer_id,
                        tenant_id=tenant_id,
                        event_type=ReputationEventType.PEER_REVIEW_GIVEN,
                        impact_score=0.5,
                        content_id=content_id,
                        metadata={"review_id": review.id}
                    )
                    
                    self.log_info(
                        "Peer review submitted",
                        reviewer_id=reviewer_id,
                        content_id=content_id,
                        review_type=review_type.value
                    )
                    
                    return {
                        "review_id": review.id,
                        "status": review.status,
                        "reviewer_impact": 0.5
                    }
                    
        except Exception as e:
            self.log_error("Peer review submission failed", reviewer_id=reviewer_id, error=e)
            raise
    
    async def award_badges(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Evaluate and award badges to user based on achievements."""
        
        try:
            with LoggedOperation("award_badges", user_id=user_id):
                # Get user statistics
                user_stats = await self._get_user_statistics(user_id, tenant_id)
                
                # Check which badges user qualifies for
                eligible_badges = []
                
                for badge_type, requirements in self._badge_requirements.items():
                    if await self._check_badge_eligibility(user_stats, badge_type, requirements):
                        # Check if user already has this badge
                        has_badge = await self._user_has_badge(user_id, tenant_id, badge_type)
                        
                        if not has_badge:
                            eligible_badges.append(badge_type)
                
                # Award eligible badges
                awarded_badges = []
                
                async with get_db_session() as session:
                    for badge_type in eligible_badges:
                        # Create badge if it doesn't exist
                        badge = await self._get_or_create_badge(badge_type, session)
                        
                        # Award badge to user
                        user_badge = UserBadge(
                            id=str(uuid.uuid4()),
                            user_id=user_id,
                            tenant_id=tenant_id,
                            badge_id=badge.id,
                            evidence=self._generate_badge_evidence(user_stats, badge_type),
                            metadata={"auto_awarded": True}
                        )
                        
                        session.add(user_badge)
                        
                        # Record reputation event
                        await self._record_reputation_event(
                            user_id=user_id,
                            tenant_id=tenant_id,
                            event_type=ReputationEventType.BADGE_EARNED,
                            impact_score=self._get_badge_reputation_impact(badge_type),
                            metadata={"badge_type": badge_type.value, "badge_id": badge.id}
                        )
                        
                        awarded_badges.append({
                            "badge_id": badge.id,
                            "badge_type": badge_type.value,
                            "name": badge.name,
                            "description": badge.description,
                            "reputation_impact": self._get_badge_reputation_impact(badge_type)
                        })
                    
                    await session.commit()
                
                self.log_info(
                    "Badges awarded",
                    user_id=user_id,
                    badges_count=len(awarded_badges)
                )
                
                return awarded_badges
                
        except Exception as e:
            self.log_error("Badge awarding failed", user_id=user_id, error=e)
            return []
    
    async def get_expert_recommendations(
        self,
        domain: str,
        tenant_id: str,
        question_context: Optional[str] = None,
        limit: int = 10,
        min_reputation: float = 70.0
    ) -> List[Dict[str, Any]]:
        """Get expert recommendations for a specific domain or question."""
        
        try:
            with LoggedOperation("get_expert_recommendations", domain=domain):
                # Get experts in the domain
                domain_experts = await self._get_domain_experts(domain, tenant_id)
                
                if not domain_experts:
                    return []
                
                # Calculate suitability scores
                expert_scores = []
                
                for expert in domain_experts:
                    # Get current reputation
                    reputation = await self.calculate_reputation_score(
                        expert["user_id"], tenant_id, 
                        ReputationCalculationMode.DOMAIN_SPECIFIC, domain
                    )
                    
                    if reputation["overall_score"] < min_reputation:
                        continue
                    
                    # Calculate availability and responsiveness
                    availability_score = await self._calculate_availability_score(
                        expert["user_id"], tenant_id
                    )
                    
                    # Calculate relevance to question context
                    relevance_score = 1.0
                    if question_context:
                        relevance_score = await self._calculate_question_relevance(
                            expert, question_context
                        )
                    
                    # Calculate composite suitability score
                    suitability_score = (
                        0.5 * (reputation["overall_score"] / 100) +
                        0.3 * availability_score +
                        0.2 * relevance_score
                    )
                    
                    expert_scores.append({
                        "expert_id": expert["id"],
                        "user_id": expert["user_id"],
                        "name": expert.get("name", "Expert"),
                        "expertise_areas": expert["expertise_areas"],
                        "reputation_score": reputation["overall_score"],
                        "availability_score": availability_score * 100,
                        "relevance_score": relevance_score * 100,
                        "suitability_score": suitability_score * 100,
                        "response_time_avg": expert.get("avg_response_time", "N/A"),
                        "success_rate": expert.get("success_rate", 0.0),
                        "badges": expert.get("badges", []),
                        "recent_contributions": expert.get("recent_contributions", 0)
                    })
                
                # Sort by suitability score
                expert_scores.sort(key=lambda x: x["suitability_score"], reverse=True)
                
                return expert_scores[:limit]
                
        except Exception as e:
            self.log_error("Expert recommendations failed", domain=domain, error=e)
            return []
    
    async def _calculate_content_quality_score(
        self,
        contributions: List[Dict[str, Any]]
    ) -> float:
        """Calculate content quality score from contributions."""
        
        if not contributions:
            return 0.0
        
        quality_scores = []
        
        for contribution in contributions:
            # Base quality from content metrics
            base_quality = contribution.get("quality_score", 0.5)
            
            # Boost for peer-reviewed content
            if contribution.get("peer_reviewed", False):
                peer_review_boost = contribution.get("avg_peer_score", 0.0) * 0.2
                base_quality += peer_review_boost
            
            # Boost for highly-rated content
            user_rating = contribution.get("avg_user_rating", 0.0)
            if user_rating > 0:
                rating_boost = (user_rating - 3.0) / 10.0  # Convert 1-5 to contribution
                base_quality += rating_boost
            
            # Recency factor
            days_old = contribution.get("days_old", 0)
            recency_factor = max(0.5, 1.0 - (days_old / 365))  # Decay over a year
            
            quality_scores.append(base_quality * recency_factor)
        
        return np.mean(quality_scores)
    
    async def _calculate_peer_review_score(
        self,
        peer_reviews: List[Dict[str, Any]]
    ) -> float:
        """Calculate score based on peer review activity and quality."""
        
        if not peer_reviews:
            return 0.0
        
        reviews_received = [r for r in peer_reviews if r["type"] == "received"]
        reviews_given = [r for r in peer_reviews if r["type"] == "given"]
        
        # Score from reviews received
        received_score = 0.0
        if reviews_received:
            avg_score = np.mean([r["avg_score"] for r in reviews_received])
            received_score = avg_score / 5.0  # Normalize to 0-1
        
        # Score from reviews given (participation)
        given_score = min(1.0, len(reviews_given) / 20.0)  # Cap at 20 reviews
        
        # Quality of reviews given (accuracy)
        review_quality_score = 0.0
        if reviews_given:
            accuracies = [r.get("accuracy", 0.5) for r in reviews_given]
            review_quality_score = np.mean(accuracies)
        
        # Combine scores
        return 0.6 * received_score + 0.2 * given_score + 0.2 * review_quality_score
    
    def _get_reputation_level(self, score: float) -> str:
        """Get reputation level based on score."""
        
        if score >= 90:
            return "Master"
        elif score >= 80:
            return "Expert"
        elif score >= 70:
            return "Advanced"
        elif score >= 60:
            return "Intermediate"
        elif score >= 40:
            return "Beginner"
        else:
            return "Novice"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check expert system health."""
        
        health = {
            "status": "healthy",
            "cached_reputations": len(self._reputation_cache),
            "cached_experts": len(self._expert_cache),
        }
        
        try:
            # Test database connectivity
            async with get_db_session() as session:
                from sqlalchemy import select, func
                
                # Count active experts
                expert_count_query = select(func.count(Expert.id)).where(
                    Expert.status == ExpertStatus.VERIFIED.value
                )
                result = await session.execute(expert_count_query)
                health["active_experts"] = result.scalar() or 0
                
                # Count recent reviews
                recent_reviews_query = select(func.count(PeerReview.id)).where(
                    PeerReview.created_at > (datetime.utcnow() - timedelta(days=7)).isoformat()
                )
                result = await session.execute(recent_reviews_query)
                health["recent_reviews"] = result.scalar() or 0
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health


# Global expert system instance
expert_system = ExpertSystemEngine()