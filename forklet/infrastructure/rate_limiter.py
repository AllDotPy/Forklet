"""
Rate limiting implementation for GitHub API requests.
"""

import time
import asyncio 
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import random

from forklet.infrastructure.logger import logger

####
##      RATE LIMIT INFO
#####
@dataclass
class RateLimitInfo:
    """Rate limit information from GitHub API headers."""
    
    limit: int = 5000
    remaining: int = 5000
    reset_time: Optional[datetime] = None
    used: int = 0
    
    @property
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""

        return self.remaining <= 10  # Keep a small buffer
    
    @property
    def reset_in_seconds(self) -> float:
        """Get seconds until rate limit resets."""

        if not self.reset_time:
            return 0.0
        return max(0.0, (self.reset_time - datetime.now()).total_seconds())


####
##      RATE LIMITER CLASS
#####
class RateLimiter:
    """
    Async rate limiter for GitHub API requests.
    
    Handles both primary and secondary rate limits with exponential backoff.
    """
    
    def __init__(
        self,
        default_delay: float = 1.0,
        max_delay: float = 60.0,
        adaptive: bool = True
    ):
        self.default_delay = default_delay
        self.max_delay = max_delay
        self.adaptive = adaptive
        self._lock = asyncio.Lock()
        self._last_request = 0.0
        self._rate_limit_info = RateLimitInfo()
        self._consecutive_limits = 0
    
    async def acquire(self) -> None:
        """Acquire rate limit permission."""

        async with self._lock:
            current_time = time.time()
            
            # Check if we need to wait due to rate limiting
            if self._rate_limit_info.is_exhausted:
                wait_time = self._rate_limit_info.reset_in_seconds
                if wait_time > 0:
                    logger.warning(
                        f"Rate limit exhausted, waiting {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)
            
            # Adaptive delay based on rate limit status
            delay = self._calculate_adaptive_delay(current_time)
            
            if delay > 0:
                await asyncio.sleep(delay)
            
            self._last_request = time.time()
    
    def _calculate_adaptive_delay(self, current_time: float) -> float:
        """Calculate adaptive delay based on rate limit status."""

        if not self.adaptive:
            return self.default_delay
        
        # Base delay from last request
        elapsed = current_time - self._last_request
        base_delay = max(0, self.default_delay - elapsed)
        
        # Adjust based on remaining rate limit
        if self._rate_limit_info.remaining < 100:
            # Very low remaining calls - be more conservative
            multiplier = 3.0

        elif self._rate_limit_info.remaining < 500:
            # Low remaining calls - moderate delay
            multiplier = 2.0

        elif self._rate_limit_info.remaining < 1000:
            # Getting low - slight increase
            multiplier = 1.5

        else:
            # Plenty of calls remaining
            multiplier = 1.0
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.8, 1.2)
        
        final_delay = min(base_delay * multiplier * jitter, self.max_delay)
        return final_delay
    
    async def update_rate_limit_info(self, headers: Dict[str, str]) -> None:
        """Update rate limit information from API response headers."""
        
        async with self._lock:
            try:
                self._rate_limit_info.limit = int(
                    headers.get('x-ratelimit-limit', 5000)
                )
                self._rate_limit_info.remaining = int(
                    headers.get('x-ratelimit-remaining', 5000)
                )
                self._rate_limit_info.used = int(
                    headers.get('x-ratelimit-used', 0)
                )
                
                reset_timestamp = headers.get('x-ratelimit-reset')
                if reset_timestamp:
                    self._rate_limit_info.reset_time = datetime.fromtimestamp(
                        int(reset_timestamp)
                    )
                
                # Track consecutive rate limit hits
                if self._rate_limit_info.is_exhausted:
                    self._consecutive_limits += 1
                else:
                    self._consecutive_limits = 0
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse rate limit headers: {e}")
    
    @property
    def rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit information."""

        return self._rate_limit_info
