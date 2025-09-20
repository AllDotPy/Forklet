"""
Rate limiting implementation for GitHub API requests.
"""

import time
import threading
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


####
##      RATE LIMIT INFO
#####
@dataclass
class RateLimitInfo:
    """Information about current rate limits."""
    
    limit: int
    remaining: int
    reset_time: datetime
    used: int = 0
    
    @property
    def seconds_until_reset(self) -> float:
        """Get seconds until rate limit resets."""

        return max(0.0, (self.reset_time - datetime.now()).total_seconds())
    
    @property
    def is_exhausted(self) -> bool:
        """Check if rate limit is exhausted."""

        return self.remaining <= 0


####
##      RATE LIMITER CLASS
#####
class RateLimiter:
    """
    Thread-safe rate limiter for GitHub API requests.
    
    Handles both primary and secondary rate limits with exponential backoff.
    """
    
    def __init__(
        self, 
        initial_delay: float = 1.0, 
        max_delay: float = 60.0
    ):
        self.lock = threading.RLock()
        self.rate_limit_info: Optional[RateLimitInfo] = None
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.current_delay = initial_delay
        self.last_request_time = 0.0
    
    def update_rate_limit_info(self, headers: dict) -> None:
        """
        Update rate limit information from HTTP headers.
        
        Args:
            headers: HTTP response headers from GitHub API
        """

        with self.lock:
            if 'X-RateLimit-Limit' in headers:
                limit = int(headers['X-RateLimit-Limit'])
                remaining = int(headers['X-RateLimit-Remaining'])
                reset_timestamp = int(headers['X-RateLimit-Reset'])
                reset_time = datetime.fromtimestamp(reset_timestamp)
                
                self.rate_limit_info = RateLimitInfo(
                    limit=limit,
                    remaining=remaining,
                    reset_time=reset_time
                )
    
    def _should_wait(self) -> bool:
        """Determine if we need to wait before making a request."""

        with self.lock:
            if not self.rate_limit_info:
                return False
            
            # Check if we're rate limited
            if self.rate_limit_info.is_exhausted:
                return True
            
            # Ensure minimum time between requests
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.current_delay:
                return True
            
            return False
    
    def _calculate_wait_time(self) -> float:
        """Calculate how long to wait before next request."""

        with self.lock:
            if (
                self.rate_limit_info 
                and self.rate_limit_info.is_exhausted
            ):
                # Wait until rate limit resets plus a buffer
                return self.rate_limit_info.seconds_until_reset + 1.0
            
            # Exponential backoff for secondary rate limits
            wait_time = self.current_delay
            self.current_delay = min(self.current_delay * 2, self.max_delay)
            return wait_time
    
    def __enter__(self) -> None:
        """Enter context manager, waiting if necessary."""

        while self._should_wait():
            wait_time = self._calculate_wait_time()
            time.sleep(wait_time)
        
        with self.lock:
            self.last_request_time = time.time()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager, resetting delay on success."""

        if exc_type is None:
            with self.lock:
                self.current_delay = self.initial_delay
    
    def reset(self) -> None:
        """Reset the rate limiter state."""
        
        with self.lock:
            self.current_delay = self.initial_delay
            self.last_request_time = 0.0
