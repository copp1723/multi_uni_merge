"""
Modern Error Handling Utilities
Standardized error handling across the application with async support
"""

import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Standardized error codes"""
    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Services
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    
    # Agent Operations
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_BUSY = "AGENT_BUSY"
    INVALID_AGENT_CONFIG = "INVALID_AGENT_CONFIG"
    
    # File Operations
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    
    # General
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"

class SwarmError(Exception):
    """Base exception class for Swarm application errors"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.now(timezone.utc).isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code.value,
                "details": self.details,
                "timestamp": self.timestamp
            }
        }

class ValidationError(SwarmError):
    """Validation error"""
    def __init__(self, message: str, field: str = None, **kwargs):
        details = {"field": field} if field else {}
        super().__init__(
            message, 
            ErrorCode.VALIDATION_ERROR, 
            details, 
            status_code=400
        )

class ServiceError(SwarmError):
    """Service-related error"""
    def __init__(self, service_name: str, message: str, **kwargs):
        details = {"service": service_name}
        super().__init__(
            message, 
            ErrorCode.SERVICE_UNAVAILABLE, 
            details, 
            status_code=503
        )

class AgentError(SwarmError):
    """Agent-related error"""
    def __init__(self, agent_id: str, message: str, **kwargs):
        details = {"agent_id": agent_id}
        super().__init__(
            message, 
            ErrorCode.AGENT_NOT_FOUND, 
            details, 
            status_code=404
        )

def handle_errors(
    default_message: str = "An error occurred",
    log_errors: bool = True,
    reraise: bool = False
):
    """
    Decorator for standardized error handling
    Supports both sync and async functions
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SwarmError:
                if reraise:
                    raise
                if log_errors:
                    logger.error(f"SwarmError in {func.__name__}: {traceback.format_exc()}")
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {traceback.format_exc()}")
                if reraise:
                    raise SwarmError(f"{default_message}: {str(e)}")
                raise SwarmError(default_message)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SwarmError:
                if reraise:
                    raise
                if log_errors:
                    logger.error(f"SwarmError in {func.__name__}: {traceback.format_exc()}")
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {traceback.format_exc()}")
                if reraise:
                    raise SwarmError(f"{default_message}: {str(e)}")
                raise SwarmError(default_message)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def create_error_response(
    error: Union[SwarmError, Exception], 
    default_status: int = 500
) -> tuple[Dict[str, Any], int]:
    """Create standardized error response"""
    if isinstance(error, SwarmError):
        return error.to_dict(), error.status_code
    else:
        return {
            "error": {
                "message": str(error),
                "code": ErrorCode.INTERNAL_ERROR.value,
                "details": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }, default_status

def log_error(
    error: Exception, 
    context: str = "", 
    extra_data: Optional[Dict[str, Any]] = None
):
    """Enhanced error logging with context"""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if extra_data:
        error_data.update(extra_data)
    
    if isinstance(error, SwarmError):
        error_data.update({
            "error_code": error.error_code.value,
            "details": error.details
        })
    
    logger.error(f"Error in {context}: {error_data}")

async def safe_async_call(
    coro, 
    default_value=None, 
    log_errors: bool = True,
    context: str = ""
):
    """Safely execute async function with error handling"""
    try:
        return await coro
    except Exception as e:
        if log_errors:
            log_error(e, context or f"async call to {coro}")
        return default_value

def safe_call(
    func, 
    *args, 
    default_value=None, 
    log_errors: bool = True,
    context: str = "",
    **kwargs
):
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            log_error(e, context or f"call to {func.__name__}")
        return default_value

class ErrorCollector:
    """Collect multiple errors for batch processing"""
    
    def __init__(self):
        self.errors = []
    
    def add_error(self, error: Union[str, SwarmError], context: str = ""):
        """Add error to collection"""
        if isinstance(error, str):
            error = SwarmError(error)
        
        self.errors.append({
            "error": error,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def get_errors(self) -> list:
        """Get all collected errors"""
        return self.errors
    
    def raise_if_errors(self, message: str = "Multiple errors occurred"):
        """Raise exception if there are errors"""
        if self.has_errors():
            error_details = {
                "error_count": len(self.errors),
                "errors": [
                    {
                        "message": err["error"].message,
                        "code": err["error"].error_code.value,
                        "context": err["context"]
                    }
                    for err in self.errors
                ]
            }
            raise SwarmError(message, ErrorCode.VALIDATION_ERROR, error_details)

# Context manager for error collection
class error_collection:
    """Context manager for collecting errors"""
    
    def __init__(self):
        self.collector = ErrorCollector()
    
    def __enter__(self):
        return self.collector
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:  # No exception occurred
            self.collector.raise_if_errors()
        return False  # Don't suppress exceptions

