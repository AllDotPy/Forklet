"""
Error handling utilities and decorators for robust operation.
"""

import functools
from typing import Callable, Any, Optional

import httpx
from github import GithubException

from forklet.infrastructure.logger import logger




####
##      DOWNLOAD ERROR MODEL
#####
class DownloadError(Exception):
    """Base exception for download-related errors."""
    
    def __init__(
        self, 
        message: str, 
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.original_error = original_error
        self.message = message
    
    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message} (Original: {self.original_error})"
        return self.message


####
##      RATE LIMITER ERROR
#####
class RateLimitError(DownloadError):
    """Exception raised when rate limits are exceeded."""
    pass


####
##      AUTHENTICATION ERROR
#####
class AuthenticationError(DownloadError):
    """Exception raised for authentication failures."""
    pass


####
##      REPO NOT FOUND ERROR
#####
class RepositoryNotFoundError(DownloadError):
    """Exception raised when repository is not found."""
    pass



####
##      RROR HANDLER UTILITIES
#####
def handle_api_error(func: Callable) -> Callable:
    """
    Decorator to handle API errors and convert to appropriate exceptions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:

        try:
            return func(*args, **kwargs)

        # Cse of GH Exceptions
        except GithubException as e:

            if e.status == 403 and 'rate limit' in str(e).lower():
                raise RateLimitError("GitHub API rate limit exceeded", e) from e

            elif e.status == 401 or e.status == 403:
                raise AuthenticationError("Authentication failed", e) from e

            elif e.status == 404:
                raise RepositoryNotFoundError("Repository not found", e) from e

            else:
                raise DownloadError(f"GitHub API error: {e}", e) from e

        # Request Exceptions
        except httpx.RequestError as e:

            if '429' in str(e) or 'rate limit' in str(e).lower():
                raise RateLimitError("Rate limit exceeded", e) from e

            else:
                raise DownloadError(f"Network error: {e}", e) from e

        except Exception as e:
            raise DownloadError(f"Unexpected error: {e}", e) from e
    
    return wrapper


def retry_on_error(max_retries: int = 3) -> Callable:
    """
    Decorator to retry operations on specific errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (
                    RateLimitError, 
                    httpx.RequestError, 
                    ConnectionError
                ) as e:
                    
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} after error: {e}"
                        )
                        continue
                    raise
                except Exception as e:
                    # Don't retry on other errors
                    raise
            
            raise last_exception or Exception("All retry attempts failed")
        return wrapper
    return decorator
