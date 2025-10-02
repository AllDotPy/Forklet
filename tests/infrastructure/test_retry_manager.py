"""
Unit tests for RetryManager in forklet.infrastructure.retry_manager.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace
from requests.exceptions import RequestException, Timeout, ConnectionError

from forklet.infrastructure.retry_manager import RetryManager, RetryConfig


# ---- Helpers ---------------------------------------------------------------

class MockAsyncFunction:
    """Helper class to create async functions with controllable behavior."""
    
    def __init__(self):
        self.call_count = 0
        self.side_effects = []
        self.return_value = "success"
    
    def set_side_effects(self, effects):
        """Set a list of exceptions to raise on each call, followed by success."""
        self.side_effects = effects
    
    async def __call__(self):
        self.call_count += 1
        
        if self.side_effects and self.call_count <= len(self.side_effects):
            effect = self.side_effects[self.call_count - 1]
            if isinstance(effect, Exception):
                raise effect
            return effect
        
        return self.return_value


# ---- RetryConfig tests -----------------------------------------------------

def test_retry_config_defaults():
    """Test RetryConfig default values."""
    config = RetryConfig()
    
    assert config.max_retries == 3
    assert config.initial_delay == 1.0
    assert config.max_delay == 30.0
    assert config.backoff_factor == 2.0
    assert RequestException in config.retryable_errors
    assert Timeout in config.retryable_errors
    assert ConnectionError in config.retryable_errors


def test_retry_config_custom_values():
    """Test RetryConfig with custom values."""
    config = RetryConfig(
        max_retries=5,
        initial_delay=0.5,
        max_delay=60.0,
        backoff_factor=3.0
    )
    
    assert config.max_retries == 5
    assert config.initial_delay == 0.5
    assert config.max_delay == 60.0
    assert config.backoff_factor == 3.0


# ---- RetryManager initialization tests -------------------------------------

def test_retry_manager_default_initialization():
    """Test RetryManager initialization with default values."""
    manager = RetryManager()
    
    assert manager.max_retries == 3
    assert manager.base_delay == 1.0
    assert manager.max_delay == 30.0
    assert manager.exponential_base == 2.0
    assert manager.jitter is True


def test_retry_manager_custom_initialization():
    """Test RetryManager initialization with custom values."""
    manager = RetryManager(
        max_retries=5,
        base_delay=0.5,
        max_delay=60.0,
        exponential_base=3.0,
        jitter=False
    )
    
    assert manager.max_retries == 5
    assert manager.base_delay == 0.5
    assert manager.max_delay == 60.0
    assert manager.exponential_base == 3.0
    assert manager.jitter is False


# ---- Successful operation tests --------------------------------------------

@pytest.mark.asyncio
async def test_successful_operation_without_retries():
    """Test that successful operation on first try requires no retries."""
    manager = RetryManager()
    mock_func = MockAsyncFunction()
    mock_func.return_value = "success_result"
    
    result = await manager.execute(mock_func)
    
    assert result == "success_result"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_successful_operation_after_retries():
    """Test successful operation after some failed attempts."""
    manager = RetryManager(max_retries=3, base_delay=0.01)  # Fast delay for testing
    mock_func = MockAsyncFunction()
    
    # Fail first 2 attempts, succeed on 3rd
    mock_func.set_side_effects([
        RequestException("Network error"),
        Timeout("Request timeout")
    ])
    mock_func.return_value = "success_after_retries"
    
    result = await manager.execute(mock_func, exceptions=(RequestException, Timeout))
    
    assert result == "success_after_retries"
    assert mock_func.call_count == 3


# ---- Retryable exceptions tests --------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("exception_class", [RequestException, Timeout, ConnectionError])
async def test_retries_on_retryable_exceptions(exception_class):
    """Test that RetryManager retries on retryable exceptions."""
    manager = RetryManager(max_retries=2, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Fail first 2 attempts with the given exception, succeed on 3rd
    mock_func.set_side_effects([
        exception_class("First failure"),
        exception_class("Second failure")
    ])
    
    result = await manager.execute(mock_func, exceptions=(exception_class,))
    
    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retries_on_multiple_exception_types():
    """Test retries work with different exception types in the same run."""
    manager = RetryManager(max_retries=3, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Fail with different exception types
    mock_func.set_side_effects([
        RequestException("Network error"),
        Timeout("Request timeout"),
        ConnectionError("Connection failed")
    ])
    
    result = await manager.execute(mock_func, exceptions=(RequestException, Timeout, ConnectionError))
    
    assert result == "success"
    assert mock_func.call_count == 4


# ---- Max attempts tests ---------------------------------------------------

@pytest.mark.asyncio
async def test_stops_retrying_after_max_attempts():
    """Test that RetryManager stops retrying after max attempts and raises the last exception."""
    manager = RetryManager(max_retries=2, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Always fail with the same exception
    exception_to_raise = RequestException("Persistent failure")
    mock_func.set_side_effects([
        exception_to_raise,
        exception_to_raise,
        exception_to_raise
    ])
    
    with pytest.raises(RequestException, match="Persistent failure"):
        await manager.execute(mock_func, exceptions=(RequestException,))
    
    # Should try 3 times (1 initial + 2 retries)
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_max_retries_override():
    """Test that max_retries parameter overrides the manager's default."""
    manager = RetryManager(max_retries=5, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Always fail
    exception_to_raise = RequestException("Always fails")
    mock_func.set_side_effects([exception_to_raise] * 10)  # More than enough failures
    
    with pytest.raises(RequestException):
        await manager.execute(mock_func, exceptions=(RequestException,), max_retries=1)
    
    # Should try 2 times (1 initial + 1 retry) due to override
    assert mock_func.call_count == 2


# ---- Non-retryable exception tests ----------------------------------------

@pytest.mark.asyncio
async def test_non_retryable_exception_raised_immediately():
    """Test that non-retryable exceptions are raised immediately without retries."""
    manager = RetryManager(max_retries=3, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Raise a ValueError which is not in the retryable exceptions
    mock_func.set_side_effects([ValueError("Non-retryable error")])
    
    with pytest.raises(ValueError, match="Non-retryable error"):
        await manager.execute(mock_func, exceptions=(RequestException, Timeout))
    
    # Should only try once
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_mixed_retryable_and_non_retryable_exceptions():
    """Test behavior when encountering non-retryable exception after retryable ones."""
    manager = RetryManager(max_retries=3, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # First attempt: retryable, second attempt: non-retryable
    mock_func.set_side_effects([
        RequestException("Retryable error"),
        ValueError("Non-retryable error")
    ])
    
    with pytest.raises(ValueError, match="Non-retryable error"):
        await manager.execute(mock_func, exceptions=(RequestException,))
    
    # Should try twice (first retry on RequestException, then fail on ValueError)
    assert mock_func.call_count == 2


# ---- Exponential backoff tests --------------------------------------------

def test_calculate_delay_exponential_growth():
    """Test that delay calculation follows exponential growth."""
    manager = RetryManager(
        base_delay=1.0,
        exponential_base=2.0,
        max_delay=100.0,
        jitter=False  # Disable jitter for predictable testing
    )
    
    # Test exponential growth: 1.0, 2.0, 4.0, 8.0
    assert manager._calculate_delay(0) == 1.0
    assert manager._calculate_delay(1) == 2.0
    assert manager._calculate_delay(2) == 4.0
    assert manager._calculate_delay(3) == 8.0


def test_calculate_delay_respects_max_delay():
    """Test that delay calculation respects the max_delay limit."""
    manager = RetryManager(
        base_delay=10.0,
        exponential_base=3.0,
        max_delay=15.0,
        jitter=False
    )
    
    # Without max_delay: attempt 2 would be 10 * 3^2 = 90
    # With max_delay of 15, it should be capped at 15
    assert manager._calculate_delay(0) == 10.0
    assert manager._calculate_delay(1) == 15.0  # Would be 30, but capped at 15
    assert manager._calculate_delay(2) == 15.0  # Would be 90, but capped at 15


def test_calculate_delay_with_jitter():
    """Test that jitter adds randomness to delay calculation."""
    manager = RetryManager(
        base_delay=10.0,
        exponential_base=2.0,
        max_delay=100.0,
        jitter=True
    )
    
    # With jitter, delay should be between 80% and 120% of base calculation
    base_calculation = 10.0  # For attempt 0
    
    delays = []
    for _ in range(100):  # Run multiple times to test randomness
        delay = manager._calculate_delay(0)
        delays.append(delay)
        # Should be between 8.0 and 12.0 (10.0 ± 20%)
        assert 8.0 <= delay <= 12.0
    
    # Verify we actually get different values (not all the same)
    assert len(set(delays)) > 1


def test_calculate_delay_custom_backoff_factor():
    """Test delay calculation with custom backoff factor."""
    manager = RetryManager(
        base_delay=2.0,
        exponential_base=3.0,  # Custom base
        max_delay=100.0,
        jitter=False
    )
    
    # Test with base 3: 2.0, 6.0, 18.0, 54.0
    assert manager._calculate_delay(0) == 2.0
    assert manager._calculate_delay(1) == 6.0
    assert manager._calculate_delay(2) == 18.0
    assert manager._calculate_delay(3) == 54.0


# ---- Integration tests -----------------------------------------------------

@pytest.mark.asyncio
async def test_real_delay_timing():
    """Test that actual delays are applied (integration test with real timing)."""
    manager = RetryManager(max_retries=2, base_delay=0.05, jitter=False)
    mock_func = MockAsyncFunction()
    
    # Fail first 2 attempts
    mock_func.set_side_effects([
        RequestException("First failure"),
        RequestException("Second failure")
    ])
    
    start_time = asyncio.get_event_loop().time()
    result = await manager.execute(mock_func, exceptions=(RequestException,))
    end_time = asyncio.get_event_loop().time()
    
    # Should have delays: 0.05 + 0.10 = 0.15 seconds minimum
    elapsed = end_time - start_time
    assert elapsed >= 0.15  # At least the expected delay time
    assert result == "success"
    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_logging_behavior(caplog):
    """Test that appropriate log messages are generated during retries."""
    manager = RetryManager(max_retries=1, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Fail once, then succeed
    mock_func.set_side_effects([RequestException("Test error")])
    
    with caplog.at_level("WARNING"):
        result = await manager.execute(mock_func, exceptions=(RequestException,))
    
    assert result == "success"
    assert "Attempt 1 failed: Test error" in caplog.text
    assert "Retrying in" in caplog.text


@pytest.mark.asyncio
async def test_logging_on_final_failure(caplog):
    """Test logging when all retries are exhausted."""
    manager = RetryManager(max_retries=1, base_delay=0.01)
    mock_func = MockAsyncFunction()
    
    # Always fail
    mock_func.set_side_effects([
        RequestException("Failure 1"),
        RequestException("Failure 2")
    ])
    
    with caplog.at_level("ERROR"):
        with pytest.raises(RequestException):
            await manager.execute(mock_func, exceptions=(RequestException,))
    
    assert "All 2 attempts failed, giving up" in caplog.text
