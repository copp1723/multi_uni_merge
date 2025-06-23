"""
Async Utilities - Modern async/await patterns and helpers
Replaces callback-based patterns with modern async/await syntax
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')

class AsyncTaskManager:
    """Manages async tasks with proper cleanup and error handling"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[str] = []
    
    async def run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """Run blocking function in executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    def create_task(self, coro: Awaitable[T], task_id: str = None) -> asyncio.Task[T]:
        """Create and track async task"""
        if task_id is None:
            task_id = f"task_{int(time.time() * 1000)}"
        
        task = asyncio.create_task(coro)
        self.running_tasks[task_id] = task
        
        # Add callback to clean up completed tasks
        task.add_done_callback(lambda t: self._task_completed(task_id))
        
        return task
    
    def _task_completed(self, task_id: str):
        """Handle task completion"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
            self.completed_tasks.append(task_id)
            
            # Keep only last 100 completed task IDs
            if len(self.completed_tasks) > 100:
                self.completed_tasks = self.completed_tasks[-100:]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel running task"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        return False
    
    async def wait_for_all(self, timeout: Optional[float] = None) -> List[Any]:
        """Wait for all running tasks to complete"""
        if not self.running_tasks:
            return []
        
        tasks = list(self.running_tasks.values())
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            return results
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for {len(tasks)} tasks")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get task manager status"""
        return {
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "max_workers": self.max_workers
        }
    
    async def cleanup(self):
        """Clean up resources"""
        # Cancel all running tasks
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)

# Global task manager instance
task_manager = AsyncTaskManager()

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for async retry logic"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

def async_timeout(seconds: float):
    """Decorator for async timeout"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds}s")
                raise
        
        return wrapper
    return decorator

async def gather_with_concurrency(
    *awaitables: Awaitable[T],
    max_concurrency: int = 10,
    return_exceptions: bool = False
) -> List[Union[T, Exception]]:
    """Gather awaitables with limited concurrency"""
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def limited_awaitable(awaitable: Awaitable[T]) -> Union[T, Exception]:
        async with semaphore:
            try:
                return await awaitable
            except Exception as e:
                if return_exceptions:
                    return e
                raise
    
    limited_awaitables = [limited_awaitable(aw) for aw in awaitables]
    return await asyncio.gather(*limited_awaitables, return_exceptions=return_exceptions)

async def async_map(
    func: Callable[[T], Awaitable[Any]],
    items: List[T],
    max_concurrency: int = 10
) -> List[Any]:
    """Async map with concurrency control"""
    awaitables = [func(item) for item in items]
    return await gather_with_concurrency(*awaitables, max_concurrency=max_concurrency)

class AsyncCache:
    """Simple async cache with TTL support"""
    
    def __init__(self, default_ttl: float = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry["expires_at"]:
                return entry["value"]
            else:
                del self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time >= entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)

def async_cached(ttl: float = 300, key_func: Optional[Callable] = None):
    """Decorator for caching async function results"""
    cache = AsyncCache(default_ttl=ttl)
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        # Add cache management methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_delete = cache.delete
        wrapper.cache_cleanup = cache.cleanup_expired
        
        return wrapper
    return decorator

class AsyncEventEmitter:
    """Simple async event emitter"""
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, listener: Callable[..., Awaitable[None]]):
        """Add event listener"""
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(listener)
    
    def off(self, event: str, listener: Callable[..., Awaitable[None]]):
        """Remove event listener"""
        if event in self.listeners:
            try:
                self.listeners[event].remove(listener)
            except ValueError:
                pass
    
    async def emit(self, event: str, *args, **kwargs):
        """Emit event to all listeners"""
        if event in self.listeners:
            tasks = []
            for listener in self.listeners[event]:
                task = asyncio.create_task(listener(*args, **kwargs))
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def remove_all_listeners(self, event: Optional[str] = None):
        """Remove all listeners for event or all events"""
        if event:
            self.listeners.pop(event, None)
        else:
            self.listeners.clear()

async def debounce_async(func: Callable[..., Awaitable[T]], delay: float) -> Callable[..., Awaitable[Optional[T]]]:
    """Async debounce function"""
    last_call_time = 0
    task: Optional[asyncio.Task] = None
    
    async def debounced(*args, **kwargs) -> Optional[T]:
        nonlocal last_call_time, task
        
        current_time = time.time()
        last_call_time = current_time
        
        if task and not task.done():
            task.cancel()
        
        async def delayed_call():
            await asyncio.sleep(delay)
            if time.time() - last_call_time >= delay:
                return await func(*args, **kwargs)
            return None
        
        task = asyncio.create_task(delayed_call())
        return await task
    
    return debounced

# Utility functions for converting sync to async
def sync_to_async(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    """Convert sync function to async"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        return await task_manager.run_in_executor(func, *args, **kwargs)
    
    return async_wrapper

async def run_sync_in_thread(func: Callable[..., T], *args, **kwargs) -> T:
    """Run sync function in thread pool"""
    return await task_manager.run_in_executor(func, *args, **kwargs)

