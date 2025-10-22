"""Structured logging configuration."""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

from src.core.config import settings


def configure_logging():
    """Configure structured logging with proper formatters and handlers."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Add custom processors
            add_request_id,
            # Final processor for output format
            structlog.processors.JSONRenderer() if getattr(settings, 'LOG_FORMAT', 'console') == "json" 
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Configure handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    handlers.append(console_handler)
    
    # File handler if configured
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when="D",  # Daily rotation
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Configure specific loggers
    configure_third_party_loggers()


def configure_third_party_loggers():
    """Configure logging levels for third-party libraries."""
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    
    # Keep important logs
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)




def add_request_id(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request ID to log entries if available."""
    
    # Try to get request ID from context variables
    import contextvars
    
    try:
        # This would be set by middleware
        request_id = contextvars.ContextVar("request_id", default=None).get()
        if request_id:
            event_dict["request_id"] = request_id
    except LookupError:
        pass
    
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_function_call(func_name: str, **kwargs):
    """Log function call with parameters."""
    logger = get_logger("function_call")
    logger.info("Function called", function=func_name, **kwargs)


def log_performance(operation: str, duration_ms: float, **kwargs):
    """Log performance metrics."""
    logger = get_logger("performance")
    logger.info(
        "Performance metric",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error with context."""
    logger = get_logger("error")
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True,
    )


def log_security_event(event_type: str, user_id: Optional[str] = None, **kwargs):
    """Log security-related events."""
    logger = get_logger("security")
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        **kwargs
    )


def log_audit_event(action: str, user_id: str, resource_type: str, 
                   resource_id: str, **kwargs):
    """Log audit events for compliance."""
    logger = get_logger("audit")
    logger.info(
        "Audit event",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        **kwargs
    )


def log_cost_tracking(operation: str, cost_usd: float, **kwargs):
    """Log cost-related events."""
    logger = get_logger("cost")
    logger.info(
        "Cost event",
        operation=operation,
        cost_usd=cost_usd,
        **kwargs
    )


def log_user_feedback(feedback_type: str, rating: Optional[float] = None, **kwargs):
    """Log user feedback events."""
    logger = get_logger("feedback")
    logger.info(
        "User feedback",
        feedback_type=feedback_type,
        rating=rating,
        **kwargs
    )


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message."""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            self.logger.error(message, exc_info=True, **kwargs)
        else:
            self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)


# Context manager for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing."""
    
    def __init__(self, operation_name: str, logger_name: str = "operation", **context):
        self.operation_name = operation_name
        self.logger = get_logger(logger_name)
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info("Operation started", operation=self.operation_name, **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        duration_ms = duration * 1000
        
        if exc_type:
            self.logger.error(
                "Operation failed",
                operation=self.operation_name,
                duration_ms=duration_ms,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context
            )
        else:
            self.logger.info(
                "Operation completed",
                operation=self.operation_name,
                duration_ms=duration_ms,
                **self.context
            )


# Initialize logging configuration
configure_logging()