"""
Retry management for network operations with exponential backoff.
"""

import time
import logging
from typing import Callable, Optional, Type, Any
from dataclasses import dataclass
from requests.exceptions import (
    RequestException, Timeout, ConnectionError
)


logger = logging.getLogger(__name__)


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
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def execute(
        self, 
        operation: Callable[[], Any], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Callable to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retries fail
        """

        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retry attempt {attempt}/{self.config.max_retries} after {delay:.2f}s"
                        )
                    time.sleep(delay)
                
                return operation(*args, **kwargs)
                
            #  Retryable errors
            except self.config.retryable_errors as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Check if we should stop retrying
                if attempt == self.config.max_retries:
                    break
                
                # Special handling for certain errors
                if isinstance(e, Timeout):
                    logger.warning("Timeout occurred, increasing delay for next attempt")
                
            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable error: {e}")
                raise
        
        # All retries failed
        logger.error(f"All {self.config.max_retries} retry attempts failed")
        raise last_exception or Exception("Retry operation failed")
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        
        delay = self.config.initial_delay * (self.config.backoff_factor ** (attempt - 1))
        return min(delay, self.config.max_delay)
