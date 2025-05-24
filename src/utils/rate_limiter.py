"""Rate limiter utility for API calls."""

import time
import asyncio
from typing import Dict, Callable, Any
from functools import wraps
from src.utils.logging_utils import agent_logger

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls: int, period: float):
        """Initialize the rate limiter.
        
        Args:
            calls (int): Number of calls allowed
            period (float): Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.timestamps: Dict[str, list] = {}
    
    def _cleanup_timestamps(self, key: str):
        """Remove timestamps older than the period."""
        now = time.time()
        self.timestamps[key] = [ts for ts in self.timestamps[key] 
                              if now - ts <= self.period]
    
    async def acquire(self, key: str):
        """Acquire permission to make an API call.
        
        Args:
            key (str): API key or identifier
        """
        if key not in self.timestamps:
            self.timestamps[key] = []
        
        self._cleanup_timestamps(key)
        
        while len(self.timestamps[key]) >= self.calls:
            # Wait until the oldest timestamp expires
            sleep_time = self.timestamps[key][0] + self.period - time.time()
            if sleep_time > 0:
                agent_logger.debug(f"Rate limit reached for {key}, waiting {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
            self._cleanup_timestamps(key)
        
        self.timestamps[key].append(time.time())

def rate_limit(calls: int, period: float):
    """Decorator for rate limiting.
    
    Args:
        calls (int): Number of calls allowed
        period (float): Time period in seconds
    """
    limiter = RateLimiter(calls, period)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            await limiter.acquire(func.__name__)
            return await func(*args, **kwargs)
        return wrapper
    return decorator 