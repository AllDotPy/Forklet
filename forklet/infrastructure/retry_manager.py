"""
Retry management for network operations with exponential backoff.
"""

import asyncio
import random
from typing import (
    Callable, Optional, Type, Awaitable, TypeVar
)
from dataclasses import dataclass
from requests.exceptions import (
    RequestException, Timeout, ConnectionError
)

from forklet.infrastructure.logger import logger

T = TypeVar('T')

####
##      RETRY CONFIG MODEL
#####
@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    retryable_errors: tuple[Type[Exception], ...] = (
        RequestException,
        Timeout,
        ConnectionError,
        ConnectionResetError,
        TimeoutError,
    )


class RetryManager:
    """
    Manages retry logic for operations with exponential backoff.
    
    Handles both transient network errors and GitHub API rate limits.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
        exceptions: tuple = (Exception,),
        max_retries: Optional[int] = None
    ) -> T:
        """
        Execute a function with retry logic.
        
        Args:
            func: Async function to execute
            exceptions: Tuple of exceptions to retry on
            max_retries: Override default max retries
            
        Returns:
            Result of the function execution
            
        Raises:
            Last exception if all retries are exhausted
        """

        max_attempts = (max_retries or self.max_retries) + 1
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except exceptions as e:
                last_exception = e
                
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    logger.error(f"All {max_attempts} attempts failed, giving up")
                    raise e
                
                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        if self.jitter:
            # Add ±20% jitter
            jitter_factor = random.uniform(0.8, 1.2)
            delay *= jitter_factor
        
        return min(delay, self.max_delay)
