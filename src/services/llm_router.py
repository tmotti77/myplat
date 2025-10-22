"""LLM router service with cost optimization, fallbacks, and circuit breakers."""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import openai
import anthropic
import google.generativeai as genai
from litellm import acompletion, get_max_tokens, token_counter

from src.core.config import settings
from src.core.logging import get_logger, LoggerMixin, log_cost_tracking
from src.services.cache import cache_service

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    LOCAL = "local"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker implementation for LLM providers."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful request."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Handle failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class LLMRouterService(LoggerMixin):
    """Service for routing LLM requests with optimization and reliability."""
    
    def __init__(self):
        self._clients = {}
        self._circuit_breakers = {}
        self._model_costs = {}
        self._model_capabilities = {}
        self._rate_limits = {}
        
        # Initialize circuit breakers for each provider
        for provider in LLMProvider:
            self._circuit_breakers[provider.value] = CircuitBreaker()
    
    async def initialize(self):
        """Initialize LLM clients and load configurations."""
        try:
            # Initialize OpenAI client
            if settings.OPENAI_API_KEY:
                self._clients[LLMProvider.OPENAI.value] = openai.AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=120.0,
                    max_retries=3
                )
            
            # Initialize Anthropic client
            if settings.ANTHROPIC_API_KEY:
                self._clients[LLMProvider.ANTHROPIC.value] = anthropic.AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY,
                    timeout=120.0,
                    max_retries=3
                )
            
            # Initialize Google client
            if settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                self._clients[LLMProvider.GOOGLE.value] = genai
            
            # Load model configurations
            await self._load_model_configurations()
            
            self.log_info(
                "LLM router initialized",
                providers=list(self._clients.keys())
            )
            
        except Exception as e:
            self.log_error("Failed to initialize LLM router", error=e)
            raise
    
    async def cleanup(self):
        """Clean up LLM router."""
        try:
            # Close client connections
            for provider, client in self._clients.items():
                if hasattr(client, 'close'):
                    await client.close()
            
            self._clients.clear()
            self.log_info("LLM router cleaned up")
            
        except Exception as e:
            self.log_error("Error during LLM router cleanup", error=e)
    
    async def route_request(
        self,
        messages: List[Dict[str, str]],
        tenant_id: str,
        user_id: Optional[str] = None,
        model_preference: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        context_requirements: Optional[Dict[str, Any]] = None,
        cost_limit: Optional[float] = None,
        latency_target: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Route LLM request to optimal model based on requirements."""
        
        start_time = time.time()
        
        try:
            # Analyze request requirements
            request_analysis = await self._analyze_request(
                messages, context_requirements
            )
            
            # Select optimal model
            selected_model = await self._select_model(
                request_analysis=request_analysis,
                tenant_id=tenant_id,
                model_preference=model_preference,
                cost_limit=cost_limit,
                latency_target=latency_target
            )
            
            if not selected_model:
                raise Exception("No suitable model available")
            
            # Check cost limits
            estimated_cost = await self._estimate_cost(
                selected_model, messages, max_tokens
            )
            
            if cost_limit and estimated_cost > cost_limit:
                # Try cheaper model
                cheaper_model = await self._find_cheaper_alternative(
                    selected_model, cost_limit, request_analysis
                )
                if cheaper_model:
                    selected_model = cheaper_model
                    estimated_cost = await self._estimate_cost(
                        selected_model, messages, max_tokens
                    )
                else:
                    raise Exception(f"Request exceeds cost limit: ${estimated_cost:.4f}")
            
            # Execute request with fallbacks
            response = await self._execute_with_fallbacks(
                model=selected_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                tenant_id=tenant_id,
                **kwargs
            )
            
            # Calculate actual cost and latency
            actual_cost = self._calculate_actual_cost(
                selected_model,
                response.get("usage", {})
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log cost tracking
            log_cost_tracking(
                "llm_completion",
                actual_cost,
                model=selected_model,
                tenant_id=tenant_id,
                user_id=user_id,
                input_tokens=response.get("usage", {}).get("prompt_tokens", 0),
                output_tokens=response.get("usage", {}).get("completion_tokens", 0),
                latency_ms=duration_ms
            )
            
            # Update rate limiting
            await self._update_rate_limits(selected_model, tenant_id)
            
            return {
                "response": response,
                "model_used": selected_model,
                "cost_usd": actual_cost,
                "latency_ms": duration_ms,
                "usage": response.get("usage", {}),
                "estimated_cost": estimated_cost,
                "routing_reason": response.get("routing_reason", "optimal_selection")
            }
            
        except Exception as e:
            self.log_error(
                "LLM routing failed",
                tenant_id=tenant_id,
                model_preference=model_preference,
                error=e
            )
            raise
    
    async def _analyze_request(
        self,
        messages: List[Dict[str, str]],
        context_requirements: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze request to determine requirements."""
        
        # Calculate total token count
        total_text = " ".join([msg.get("content", "") for msg in messages])
        estimated_tokens = len(total_text.split()) * 1.3  # Rough estimation
        
        # Detect language
        language = self._detect_language(total_text)
        
        # Determine content type
        content_type = self._determine_content_type(total_text)
        
        # Check for sensitive content
        is_sensitive = self._check_sensitive_content(total_text)
        
        return {
            "estimated_input_tokens": int(estimated_tokens),
            "language": language,
            "content_type": content_type,
            "is_sensitive": is_sensitive,
            "requires_long_context": estimated_tokens > 8000,
            "requires_code_capabilities": "code" in content_type,
            "requires_reasoning": self._requires_reasoning(total_text),
            "context_requirements": context_requirements or {}
        }
    
    async def _select_model(
        self,
        request_analysis: Dict[str, Any],
        tenant_id: str,
        model_preference: Optional[str] = None,
        cost_limit: Optional[float] = None,
        latency_target: Optional[float] = None
    ) -> Optional[str]:
        """Select optimal model based on request analysis."""
        
        # Get available models
        available_models = await self._get_available_models(tenant_id)
        
        if not available_models:
            return None
        
        # Apply user preference if specified and available
        if model_preference and model_preference in available_models:
            # Check if preferred model meets requirements
            if await self._model_meets_requirements(model_preference, request_analysis):
                return model_preference
        
        # Score models based on requirements
        model_scores = {}
        
        for model in available_models:
            score = await self._score_model(
                model, request_analysis, cost_limit, latency_target
            )
            if score > 0:  # Only consider viable models
                model_scores[model] = score
        
        if not model_scores:
            return None
        
        # Return highest scoring model
        return max(model_scores.items(), key=lambda x: x[1])[0]
    
    async def _score_model(
        self,
        model: str,
        request_analysis: Dict[str, Any],
        cost_limit: Optional[float],
        latency_target: Optional[float]
    ) -> float:
        """Score model suitability for request."""
        
        score = 0.0
        
        # Get model capabilities
        capabilities = self._model_capabilities.get(model, {})
        
        # Base capability score
        if capabilities.get("supports_chat", True):
            score += 1.0
        
        # Language support
        if request_analysis["language"] in capabilities.get("languages", ["en"]):
            score += 2.0
        elif request_analysis["language"] == "en":
            score += 1.0
        
        # Context window requirement
        if request_analysis["requires_long_context"]:
            if capabilities.get("max_context_tokens", 4000) >= 32000:
                score += 2.0
            elif capabilities.get("max_context_tokens", 4000) >= 16000:
                score += 1.0
            else:
                score -= 2.0  # Penalize insufficient context
        
        # Code capabilities
        if request_analysis["requires_code_capabilities"]:
            if capabilities.get("code_support", False):
                score += 1.5
            else:
                score -= 1.0
        
        # Reasoning capabilities
        if request_analysis["requires_reasoning"]:
            reasoning_score = capabilities.get("reasoning_score", 0.5)
            score += reasoning_score * 2.0
        
        # Cost efficiency
        if cost_limit:
            estimated_cost = self._model_costs.get(model, {}).get("per_1k_tokens", 0.01)
            if estimated_cost <= cost_limit:
                score += 1.0 - (estimated_cost / cost_limit)  # Higher score for cheaper models
            else:
                return 0.0  # Exclude if over budget
        
        # Latency requirement
        if latency_target:
            avg_latency = capabilities.get("avg_latency_ms", 2000)
            if avg_latency <= latency_target:
                score += 1.0 - (avg_latency / latency_target)
            else:
                score -= 0.5  # Slight penalty for slower models
        
        # Provider health (circuit breaker state)
        provider = self._get_model_provider(model)
        circuit_breaker = self._circuit_breakers.get(provider)
        if circuit_breaker and circuit_breaker.state == CircuitBreakerState.OPEN:
            return 0.0  # Exclude unhealthy providers
        elif circuit_breaker and circuit_breaker.state == CircuitBreakerState.HALF_OPEN:
            score *= 0.5  # Reduce preference for recovering providers
        
        return max(0.0, score)
    
    async def _execute_with_fallbacks(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: float,
        tenant_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute LLM request with fallback models."""
        
        # Get fallback models
        fallback_models = await self._get_fallback_models(model, tenant_id)
        models_to_try = [model] + fallback_models
        
        last_error = None
        
        for attempt_model in models_to_try:
            try:
                provider = self._get_model_provider(attempt_model)
                circuit_breaker = self._circuit_breakers[provider]
                
                # Execute with circuit breaker protection
                response = await circuit_breaker.call(
                    self._execute_llm_request,
                    attempt_model,
                    messages,
                    max_tokens,
                    temperature,
                    **kwargs
                )
                
                # Add routing information
                if attempt_model != model:
                    response["routing_reason"] = f"fallback_from_{model}_to_{attempt_model}"
                
                return response
                
            except Exception as e:
                last_error = e
                self.log_warning(
                    "LLM request failed, trying fallback",
                    model=attempt_model,
                    fallback_available=len(models_to_try) > 1,
                    error=str(e)
                )
                continue
        
        # All models failed
        raise Exception(f"All LLM requests failed. Last error: {last_error}")
    
    async def _execute_llm_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        temperature: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute LLM request to specific model."""
        
        try:
            # Use LiteLLM for unified interface
            response = await acompletion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return {
                "choices": response.choices,
                "usage": response.usage.dict() if response.usage else {},
                "model": response.model,
                "id": response.id,
                "created": response.created,
            }
            
        except Exception as e:
            self.log_error(
                "LLM request execution failed",
                model=model,
                error=e
            )
            raise
    
    async def _load_model_configurations(self):
        """Load model capabilities and cost information."""
        
        # Model costs (per 1K tokens) - approximate values
        self._model_costs = {
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro-vision": {"input": 0.0005, "output": 0.0015},
        }
        
        # Model capabilities
        self._model_capabilities = {
            "gpt-4-turbo-preview": {
                "max_context_tokens": 128000,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.9,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "avg_latency_ms": 3000,
            },
            "gpt-4": {
                "max_context_tokens": 8192,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.95,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "avg_latency_ms": 4000,
            },
            "gpt-3.5-turbo": {
                "max_context_tokens": 16384,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.7,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "avg_latency_ms": 1500,
            },
            "claude-3-opus": {
                "max_context_tokens": 200000,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.95,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "avg_latency_ms": 5000,
            },
            "claude-3-sonnet": {
                "max_context_tokens": 200000,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.85,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "avg_latency_ms": 3000,
            },
            "claude-3-haiku": {
                "max_context_tokens": 200000,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.75,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "avg_latency_ms": 1000,
            },
            "gemini-pro": {
                "max_context_tokens": 32768,
                "supports_chat": True,
                "code_support": True,
                "reasoning_score": 0.8,
                "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "hi", "ar"],
                "avg_latency_ms": 2000,
            },
        }
    
    async def _get_available_models(self, tenant_id: str) -> List[str]:
        """Get available models for tenant."""
        
        available = []
        
        # Check each provider's availability
        for provider, client in self._clients.items():
            if client:
                # Get models for this provider
                provider_models = self._get_provider_models(provider)
                
                # Check circuit breaker
                circuit_breaker = self._circuit_breakers[provider]
                if circuit_breaker.state != CircuitBreakerState.OPEN:
                    available.extend(provider_models)
        
        return available
    
    def _get_provider_models(self, provider: str) -> List[str]:
        """Get available models for provider."""
        
        models_by_provider = {
            LLMProvider.OPENAI.value: [
                "gpt-4-turbo-preview",
                "gpt-4",
                "gpt-3.5-turbo"
            ],
            LLMProvider.ANTHROPIC.value: [
                "claude-3-opus",
                "claude-3-sonnet", 
                "claude-3-haiku"
            ],
            LLMProvider.GOOGLE.value: [
                "gemini-pro",
                "gemini-pro-vision"
            ],
        }
        
        return models_by_provider.get(provider, [])
    
    def _get_model_provider(self, model: str) -> str:
        """Get provider for model."""
        
        if model.startswith("gpt"):
            return LLMProvider.OPENAI.value
        elif model.startswith("claude"):
            return LLMProvider.ANTHROPIC.value
        elif model.startswith("gemini"):
            return LLMProvider.GOOGLE.value
        elif model.startswith("command"):
            return LLMProvider.COHERE.value
        else:
            return LLMProvider.LOCAL.value
    
    async def _get_fallback_models(
        self,
        primary_model: str,
        tenant_id: str
    ) -> List[str]:
        """Get fallback models for primary model."""
        
        # Define fallback hierarchy
        fallback_hierarchy = {
            "gpt-4-turbo-preview": ["gpt-4", "claude-3-sonnet", "gpt-3.5-turbo"],
            "gpt-4": ["gpt-3.5-turbo", "claude-3-haiku"],
            "claude-3-opus": ["claude-3-sonnet", "gpt-4", "claude-3-haiku"],
            "claude-3-sonnet": ["claude-3-haiku", "gpt-3.5-turbo"],
            "gemini-pro": ["gpt-3.5-turbo", "claude-3-haiku"],
        }
        
        fallbacks = fallback_hierarchy.get(primary_model, ["gpt-3.5-turbo"])
        available_models = await self._get_available_models(tenant_id)
        
        # Filter to only available models
        return [model for model in fallbacks if model in available_models]
    
    async def _estimate_cost(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int]
    ) -> float:
        """Estimate cost for LLM request."""
        
        costs = self._model_costs.get(model, {"input": 0.01, "output": 0.03})
        
        # Estimate input tokens
        total_text = " ".join([msg.get("content", "") for msg in messages])
        input_tokens = len(total_text.split()) * 1.3  # Rough estimation
        
        # Estimate output tokens
        output_tokens = max_tokens or 1000
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def _calculate_actual_cost(self, model: str, usage: Dict[str, Any]) -> float:
        """Calculate actual cost from usage."""
        
        costs = self._model_costs.get(model, {"input": 0.01, "output": 0.03})
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    async def _find_cheaper_alternative(
        self,
        model: str,
        cost_limit: float,
        request_analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Find cheaper alternative model that meets requirements."""
        
        # Get all available models sorted by cost
        available_models = await self._get_available_models(request_analysis.get("tenant_id"))
        
        # Sort by cost (ascending)
        sorted_models = sorted(
            available_models,
            key=lambda m: self._model_costs.get(m, {"input": 0.01}).get("input", 0.01)
        )
        
        for alternative in sorted_models:
            if alternative == model:
                continue
            
            # Check if it meets requirements
            if await self._model_meets_requirements(alternative, request_analysis):
                # Check cost
                estimated_cost = await self._estimate_cost(
                    alternative, [], request_analysis.get("max_tokens")
                )
                if estimated_cost <= cost_limit:
                    return alternative
        
        return None
    
    async def _model_meets_requirements(
        self,
        model: str,
        request_analysis: Dict[str, Any]
    ) -> bool:
        """Check if model meets request requirements."""
        
        capabilities = self._model_capabilities.get(model, {})
        
        # Check context window
        if request_analysis["requires_long_context"]:
            if capabilities.get("max_context_tokens", 4000) < 16000:
                return False
        
        # Check language support
        if request_analysis["language"] not in capabilities.get("languages", ["en"]):
            if request_analysis["language"] != "en":  # English is usually supported
                return False
        
        # Check code capabilities
        if request_analysis["requires_code_capabilities"]:
            if not capabilities.get("code_support", False):
                return False
        
        return True
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text (simplified)."""
        
        # This is a simplified implementation
        # In production, use proper language detection library
        
        hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        
        total_chars = len(text)
        
        if total_chars > 0:
            if hebrew_chars / total_chars > 0.1:
                return "he"
            elif arabic_chars / total_chars > 0.1:
                return "ar"
        
        return "en"  # Default to English
    
    def _determine_content_type(self, text: str) -> List[str]:
        """Determine content type from text."""
        
        types = []
        
        # Check for code
        code_indicators = ["def ", "function ", "class ", "import ", "SELECT ", "```"]
        if any(indicator in text for indicator in code_indicators):
            types.append("code")
        
        # Check for math
        math_indicators = ["∫", "∑", "∂", "√", "π", "equation", "formula"]
        if any(indicator in text for indicator in math_indicators):
            types.append("math")
        
        # Default
        if not types:
            types.append("general")
        
        return types
    
    def _check_sensitive_content(self, text: str) -> bool:
        """Check for sensitive content (simplified)."""
        
        sensitive_keywords = [
            "password", "secret", "confidential", "classified",
            "ssn", "social security", "credit card"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in sensitive_keywords)
    
    def _requires_reasoning(self, text: str) -> bool:
        """Check if request requires complex reasoning."""
        
        reasoning_indicators = [
            "analyze", "compare", "explain why", "reasoning",
            "logic", "deduce", "infer", "conclusion"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in reasoning_indicators)
    
    async def _update_rate_limits(self, model: str, tenant_id: str):
        """Update rate limiting counters."""
        
        try:
            # Track requests per minute
            cache_key = f"rate_limit:{model}:{tenant_id}:{int(time.time() // 60)}"
            await cache_service.increment(cache_key)
            await cache_service.expire(cache_key, 60)
            
        except Exception as e:
            self.log_warning("Failed to update rate limits", error=e)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check LLM router health."""
        
        health = {
            "status": "healthy",
            "providers": {},
            "circuit_breakers": {},
            "models_available": 0,
        }
        
        # Check each provider
        for provider, client in self._clients.items():
            provider_health = {
                "available": client is not None,
                "models": self._get_provider_models(provider)
            }
            health["providers"][provider] = provider_health
        
        # Check circuit breakers
        for provider, cb in self._circuit_breakers.items():
            health["circuit_breakers"][provider] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count
            }
        
        # Count available models
        try:
            available_models = await self._get_available_models("default")
            health["models_available"] = len(available_models)
        except Exception:
            health["models_available"] = 0
        
        # Overall status
        if health["models_available"] == 0:
            health["status"] = "unhealthy"
        elif any(cb.state == CircuitBreakerState.OPEN for cb in self._circuit_breakers.values()):
            health["status"] = "degraded"
        
        return health


# Global LLM router service instance
llm_router_service = LLMRouterService()