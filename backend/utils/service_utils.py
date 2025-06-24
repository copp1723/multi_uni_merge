"""
Service Utilities - Common patterns and helpers for service management
Refactored from repeated code patterns across services
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .error_handler import SwarmError, ErrorCode, handle_errors
from .async_utils import async_retry, AsyncCache

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class ServiceHealth:
    """Service health information"""
    status: ServiceStatus
    message: str
    details: Dict[str, Any]
    last_check: str
    response_time_ms: Optional[float] = None

class BaseService(ABC):
    """Base service class with common functionality"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")
        self._health_cache = AsyncCache(default_ttl=30)  # 30 second cache
        self._last_health_check = None
        self._metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "avg_response_time": 0.0,
            "last_request_time": None
        }
    
    @abstractmethod
    async def _health_check(self) -> ServiceHealth:
        """Implement service-specific health check"""
        pass
    
    @handle_errors("Health check failed")
    async def get_health(self, use_cache: bool = True) -> ServiceHealth:
        """Get service health with caching"""
        cache_key = f"{self.service_name}_health"
        
        if use_cache:
            cached_health = await self._health_cache.get(cache_key)
            if cached_health:
                return cached_health
        
        start_time = time.time()
        health = await self._health_check()
        response_time = (time.time() - start_time) * 1000
        
        health.response_time_ms = response_time
        health.last_check = datetime.now(timezone.utc).isoformat()
        
        await self._health_cache.set(cache_key, health)
        self._last_health_check = health
        
        return health
    
    def _record_request(self, success: bool = True, response_time: float = 0.0):
        """Record request metrics"""
        self._metrics["requests_total"] += 1
        if not success:
            self._metrics["requests_failed"] += 1
        
        # Update average response time
        if response_time > 0:
            current_avg = self._metrics["avg_response_time"]
            total_requests = self._metrics["requests_total"]
            self._metrics["avg_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
        
        self._metrics["last_request_time"] = datetime.now(timezone.utc).isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            "service_name": self.service_name,
            "metrics": self._metrics.copy(),
            "last_health_check": self._last_health_check.status.value if self._last_health_check else None
        }
    
    async def test_connection(self) -> bool:
        """Test service connection"""
        try:
            health = await self.get_health(use_cache=False)
            return health.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

class ServiceRegistry:
    """Registry for managing multiple services"""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.logger = logging.getLogger(f"{__name__}.ServiceRegistry")
    
    def register(self, service: BaseService):
        """Register a service"""
        self.services[service.service_name] = service
        self.logger.info(f"✅ Registered service: {service.service_name}")
    
    def unregister(self, service_name: str):
        """Unregister a service"""
        if service_name in self.services:
            del self.services[service_name]
            self.logger.info(f"❌ Unregistered service: {service_name}")
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get service by name"""
        return self.services.get(service_name)
    
    async def get_all_health(self) -> Dict[str, ServiceHealth]:
        """Get health status of all services"""
        health_status = {}
        
        for name, service in self.services.items():
            try:
                health = await service.get_health()
                health_status[name] = health
            except Exception as e:
                health_status[name] = ServiceHealth(
                    status=ServiceStatus.ERROR,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e)},
                    last_check=datetime.now(timezone.utc).isoformat()
                )
        
        return health_status
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        all_health = await self.get_all_health()
        
        healthy_count = sum(1 for h in all_health.values() if h.status == ServiceStatus.HEALTHY)
        total_count = len(all_health)
        
        if healthy_count == total_count:
            overall_status = ServiceStatus.HEALTHY
        elif healthy_count > 0:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.UNHEALTHY
        
        return {
            "overall_status": overall_status.value,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": {name: health.status.value for name, health in all_health.items()},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global service registry
service_registry = ServiceRegistry()

def validate_config(config: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate service configuration"""
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        raise SwarmError(
            f"Missing required configuration fields: {', '.join(missing_fields)}",
            ErrorCode.VALIDATION_ERROR,
            {"missing_fields": missing_fields}
        )

def format_api_response(
    data: Any = None,
    message: str = "Success",
    status: str = "success",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format standardized API response"""
    response = {
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata:
        response["metadata"] = metadata
    
    return response

def paginate_results(
    items: List[Any],
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, Any]:
    """Paginate list of items"""
    # Validate parameters
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_items = items[start_idx:end_idx]
    
    return {
        "items": paginated_items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        current_time = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(current_time)
            return True
        
        return False
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        if identifier not in self.requests:
            return self.max_requests
        
        current_time = time.time()
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(recent_requests))

def sanitize_input(
    data: Union[str, Dict[str, Any]],
    max_length: int = 10000,
    allowed_keys: Optional[List[str]] = None
) -> Union[str, Dict[str, Any]]:
    """Sanitize user input"""
    if isinstance(data, str):
        # Truncate long strings
        if len(data) > max_length:
            data = data[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            data = data.replace(char, '')
        
        return data.strip()
    
    elif isinstance(data, dict):
        sanitized = {}
        
        for key, value in data.items():
            # Skip keys not in allowed list
            if allowed_keys and key not in allowed_keys:
                continue
            
            # Recursively sanitize values
            if isinstance(value, (str, dict)):
                sanitized[key] = sanitize_input(value, max_length, allowed_keys)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_input(item, max_length, allowed_keys)
                    if isinstance(item, (str, dict)) else item
                    for item in value[:100]  # Limit list size
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    return data

def generate_correlation_id() -> str:
    """Generate correlation ID for request tracking"""
    import uuid
    return str(uuid.uuid4())

def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionaries"""
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'token', 'api_key', 'secret', 'private_key',
            'authorization', 'auth', 'credential', 'key'
        ]
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive information
        if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                masked_data[key] = f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"
            else:
                masked_data[key] = "***"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value, sensitive_keys)
    
    return masked_data

