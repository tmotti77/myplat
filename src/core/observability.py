"""Production observability with simplified monitoring and Prometheus metrics."""
import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)

# Global observability components - simplified for stable deployment

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'tenant_id'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

RAG_OPERATIONS = Counter(
    'rag_operations_total',
    'Total RAG operations',
    ['operation_type', 'tenant_id', 'success']
)

RAG_LATENCY = Histogram(
    'rag_operation_duration_seconds',
    'RAG operation duration',
    ['operation_type', 'tenant_id'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'tenant_id', 'success']
)

LLM_COST = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model', 'tenant_id']
)

EMBEDDING_OPERATIONS = Counter(
    'embedding_operations_total',
    'Total embedding operations',
    ['model', 'tenant_id', 'cache_hit']
)

SEARCH_OPERATIONS = Counter(
    'search_operations_total',
    'Total search operations',
    ['search_type', 'tenant_id']
)

DOCUMENT_PROCESSING = Counter(
    'document_processing_total',
    'Total document processing operations',
    ['document_type', 'tenant_id', 'success']
)

FEEDBACK_EVENTS = Counter(
    'feedback_events_total',
    'Total feedback events',
    ['feedback_type', 'tenant_id']
)

ACTIVE_USERS = Gauge(
    'active_users_current',
    'Current active users',
    ['tenant_id']
)

SYSTEM_HEALTH = Gauge(
    'system_health_score',
    'Overall system health score (0-1)',
    ['component']
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections',
    ['pool_name']
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'cache_type', 'hit']
)


class ObservabilityManager:
    """Centralized observability management for the platform."""
    
    def __init__(self):
        self.initialized = False
        self.prometheus_port = 8001  # Changed to avoid conflict with main app
        
    async def initialize(self, app=None):
        """Initialize simplified observability stack."""
        
        if self.initialized:
            return
        
        try:
            # Start Prometheus metrics server if enabled
            if getattr(settings, 'ENABLE_PROMETHEUS', True):
                start_http_server(self.prometheus_port)
                logger.info("Prometheus metrics server started", port=self.prometheus_port)
            
            self.initialized = True
            logger.info("Observability stack initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize observability", error=str(e))
            # Don't raise - allow system to continue without full observability
    
    
    def record_rag_operation(
        self,
        operation_type: str,
        tenant_id: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ):
        """Record RAG operation metrics."""
        
        # Prometheus metrics
        RAG_OPERATIONS.labels(
            operation_type=operation_type,
            tenant_id=tenant_id,
            success=str(success)
        ).inc()
        
        RAG_LATENCY.labels(
            operation_type=operation_type,
            tenant_id=tenant_id
        ).observe(duration_ms / 1000.0)
        
    
    def record_llm_request(
        self,
        provider: str,
        model: str,
        tenant_id: str,
        success: bool,
        cost_usd: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0
    ):
        """Record LLM request metrics."""
        
        LLM_REQUESTS.labels(
            provider=provider,
            model=model,
            tenant_id=tenant_id,
            success=str(success)
        ).inc()
        
        if cost_usd > 0:
            LLM_COST.labels(
                provider=provider,
                model=model,
                tenant_id=tenant_id
            ).inc(cost_usd)
        
    
    def record_embedding_operation(
        self,
        model: str,
        tenant_id: str,
        cache_hit: bool,
        batch_size: int = 1
    ):
        """Record embedding operation metrics."""
        
        EMBEDDING_OPERATIONS.labels(
            model=model,
            tenant_id=tenant_id,
            cache_hit=str(cache_hit)
        ).inc(batch_size)
    
    def record_search_operation(
        self,
        search_type: str,
        tenant_id: str,
        results_count: int = 0
    ):
        """Record search operation metrics."""
        
        SEARCH_OPERATIONS.labels(
            search_type=search_type,
            tenant_id=tenant_id
        ).inc()
    
    def record_document_processing(
        self,
        document_type: str,
        tenant_id: str,
        success: bool,
        processing_time_ms: float = 0.0
    ):
        """Record document processing metrics."""
        
        DOCUMENT_PROCESSING.labels(
            document_type=document_type,
            tenant_id=tenant_id,
            success=str(success)
        ).inc()
    
    def record_feedback_event(
        self,
        feedback_type: str,
        tenant_id: str
    ):
        """Record feedback event metrics."""
        
        FEEDBACK_EVENTS.labels(
            feedback_type=feedback_type,
            tenant_id=tenant_id
        ).inc()
    
    def update_active_users(self, tenant_id: str, count: int):
        """Update active users gauge."""
        
        ACTIVE_USERS.labels(tenant_id=tenant_id).set(count)
    
    def update_system_health(self, component: str, health_score: float):
        """Update system health score."""
        
        SYSTEM_HEALTH.labels(component=component).set(health_score)
    
    def update_database_connections(self, pool_name: str, count: int):
        """Update database connection count."""
        
        DATABASE_CONNECTIONS.labels(pool_name=pool_name).set(count)
    
    def record_cache_operation(
        self,
        operation: str,
        cache_type: str,
        hit: bool
    ):
        """Record cache operation metrics."""
        
        CACHE_OPERATIONS.labels(
            operation=operation,
            cache_type=cache_type,
            hit=str(hit)
        ).inc()


# Global observability manager instance
observability = ObservabilityManager()


def trace_operation(operation_name: str, **attributes):
    """Decorator for logging operations (simplified without OpenTelemetry)."""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Operation completed: {operation_name}",
                    duration_ms=duration * 1000,
                    success=True,
                    **attributes
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation failed: {operation_name}",
                    duration_ms=duration * 1000,
                    success=False,
                    error=str(e),
                    **attributes
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Operation completed: {operation_name}",
                    duration_ms=duration * 1000,
                    success=True,
                    **attributes
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Operation failed: {operation_name}",
                    duration_ms=duration * 1000,
                    success=False,
                    error=str(e),
                    **attributes
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


@asynccontextmanager
async def trace_span(span_name: str, **attributes):
    """Context manager for logging operations (simplified without OpenTelemetry)."""
    
    start_time = time.time()
    logger.info(f"Starting operation: {span_name}", **attributes)
    
    try:
        yield None
        duration = time.time() - start_time
        logger.info(
            f"Operation completed: {span_name}",
            duration_ms=duration * 1000,
            **attributes
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Operation failed: {span_name}",
            duration_ms=duration * 1000,
            error=str(e),
            **attributes
        )
        raise


def time_operation(metric_name: str, labels: Dict[str, str] = None):
    """Decorator for timing operations with Prometheus metrics."""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
                
            except Exception as e:
                success = False
                raise
                
            finally:
                duration = time.time() - start_time
                
                # Record in appropriate histogram
                if metric_name == "rag_operation":
                    RAG_LATENCY.labels(**(labels or {})).observe(duration)
                elif metric_name == "http_request":
                    REQUEST_DURATION.labels(**(labels or {})).observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
                
            finally:
                duration = time.time() - start_time
                
                if metric_name == "rag_operation":
                    RAG_LATENCY.labels(**(labels or {})).observe(duration)
                elif metric_name == "http_request":
                    REQUEST_DURATION.labels(**(labels or {})).observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


async def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics."""
    
    import psutil
    
    # System resource metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Network metrics
    network = psutil.net_io_counters()
    
    return {
        "timestamp": time.time(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024**3)
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
    }


async def health_check_all_services() -> Dict[str, Any]:
    """Perform health check on all system services."""
    
    health_status = {
        "overall": "healthy",
        "timestamp": time.time(),
        "services": {}
    }
    
    services_to_check = [
        ("database", "src.core.database", "check_database_health"),
        ("redis", "src.services.cache", "cache_service.health_check"),
        ("vector_store", "src.services.vector_store", "vector_store_service.health_check"),
        ("llm_router", "src.services.llm_router", "llm_router_service.health_check"),
        ("search", "src.services.search", "search_service.health_check"),
        ("rag_engine", "src.services.rag_engine", "rag_engine.health_check"),
        ("personalization", "src.services.personalization", "personalization_engine.health_check"),
        ("expert_system", "src.services.expert_system", "expert_system.health_check"),
        ("feedback_system", "src.services.feedback_system", "feedback_system.health_check")
    ]
    
    unhealthy_count = 0
    
    for service_name, module_path, health_method in services_to_check:
        try:
            # Dynamic import and health check
            module = __import__(module_path, fromlist=[health_method.split('.')[0]])
            
            if '.' in health_method:
                obj_name, method_name = health_method.split('.')
                obj = getattr(module, obj_name)
                health_func = getattr(obj, method_name)
            else:
                health_func = getattr(module, health_method)
            
            if asyncio.iscoroutinefunction(health_func):
                health_result = await health_func()
            else:
                health_result = health_func()
            
            health_status["services"][service_name] = health_result
            
            # Update system health metric
            if isinstance(health_result, dict):
                service_health = 1.0 if health_result.get("status") == "healthy" else 0.0
            else:
                service_health = 1.0 if health_result else 0.0
            
            observability.update_system_health(service_name, service_health)
            
            if service_health < 1.0:
                unhealthy_count += 1
                
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "error",
                "error": str(e)
            }
            observability.update_system_health(service_name, 0.0)
            unhealthy_count += 1
    
    # Overall health determination
    if unhealthy_count == 0:
        health_status["overall"] = "healthy"
    elif unhealthy_count <= 2:
        health_status["overall"] = "degraded"
    else:
        health_status["overall"] = "unhealthy"
    
    # Update overall system health
    overall_health_score = max(0.0, 1.0 - (unhealthy_count / len(services_to_check)))
    observability.update_system_health("overall", overall_health_score)
    
    return health_status