# tests/infrastructure/test_rate_limiter.py

import time
import random
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest

# Adjust this import path to match your project's structure
from forklet.infrastructure.rate_limiter import RateLimiter, RateLimitInfo

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


## 1. RateLimitInfo Helper Class Tests
# ------------------------------------

def test_rate_limit_info_is_exhausted():
    """Test the 'is_exhausted' property logic."""
    info = RateLimitInfo()
    info.remaining = 11
    assert not info.is_exhausted, "Should not be exhausted when remaining is > 10"

    info.remaining = 10
    assert info.is_exhausted, "Should be exhausted when remaining is <= 10"

    info.remaining = 0
    assert info.is_exhausted, "Should be exhausted when remaining is 0"


def test_rate_limit_info_reset_in_seconds():
    """Test the calculation of seconds until reset."""
    info = RateLimitInfo()
    
    # Mock datetime.now() to control the current time for the test
    mock_now = datetime(2025, 10, 2, 12, 0, 0)
    with patch('forklet.infrastructure.rate_limiter.datetime', autospec=True) as mock_datetime:
        mock_datetime.now.return_value = mock_now

        # Set reset_time 30 seconds into the future
        info.reset_time = mock_now + timedelta(seconds=30)
        assert info.reset_in_seconds == 30.0

        # Set reset_time in the past
        info.reset_time = mock_now - timedelta(seconds=30)
        assert info.reset_in_seconds == 0.0, "Should not return negative time"

        # No reset time set
        info.reset_time = None
        assert info.reset_in_seconds == 0.0


## 2. RateLimiter Initialization Test
# ------------------------------------

def test_ratelimiter_initialization():
    """Ensure the RateLimiter initializes with correct default values."""
    rl = RateLimiter(default_delay=0.5, max_delay=30.0, adaptive=False)
    assert rl.default_delay == 0.5
    assert rl.max_delay == 30.0
    assert not rl.adaptive


## 3. Update from Headers Tests
# ------------------------------

async def test_update_rate_limit_info_sets_values_correctly():
    """Test that rate limit info is correctly parsed from headers."""
    rl = RateLimiter()
    reset_timestamp = int(time.time()) + 60
    
    headers = {
        "x-ratelimit-limit": "5000",
        "x-ratelimit-remaining": "4500",
        "x-ratelimit-used": "500",
        "x-ratelimit-reset": str(reset_timestamp),
    }
    
    await rl.update_rate_limit_info(headers)
    info = rl.rate_limit_info
    
    assert info.limit == 5000
    assert info.remaining == 4500
    assert info.used == 500
    assert info.reset_time == datetime.fromtimestamp(reset_timestamp)
    assert not info.is_exhausted


async def test_update_rate_limit_increments_consecutive_limits():
    """Test that _consecutive_limits is handled correctly."""
    rl = RateLimiter()
    exhausted_headers = {"x-ratelimit-remaining": "5"}
    ok_headers = {"x-ratelimit-remaining": "100"}

    await rl.update_rate_limit_info(exhausted_headers)
    assert rl._consecutive_limits == 1

    await rl.update_rate_limit_info(exhausted_headers)
    assert rl._consecutive_limits == 2

    await rl.update_rate_limit_info(ok_headers)
    assert rl._consecutive_limits == 0, "Counter should reset when not exhausted"


## 4. Acquire Logic and Wait Behavior Tests
# ------------------------------------------

@patch('asyncio.sleep', new_callable=AsyncMock)
async def test_acquire_waits_when_primary_rate_limit_exhausted(mock_sleep):
    """Test that acquire() waits for reset_in_seconds when exhausted."""
    rl = RateLimiter()
    
    # Mock datetime.now() to control time
    mock_now = datetime(2025, 10, 2, 12, 0, 0)
    with patch('forklet.infrastructure.rate_limiter.datetime', autospec=True) as mock_datetime:
        mock_datetime.now.return_value = mock_now

        # Set state to exhausted, with reset 15 seconds in the future
        rl.rate_limit_info.remaining = 5
        rl.rate_limit_info.reset_time = mock_now + timedelta(seconds=15)

        await rl.acquire()
        
        # Check that it slept for the primary rate limit duration
        mock_sleep.assert_any_call(15.0)


@patch('asyncio.sleep', new_callable=AsyncMock)
async def test_acquire_uses_adaptive_delay(mock_sleep):
    """Test that acquire() uses the calculated adaptive delay."""
    rl = RateLimiter(default_delay=1.0)
    
    # Mock time.time() for delay calculation
    with patch('time.time', side_effect=[1000.0, 1000.1]):
        # Ensure rate limit is not exhausted
        rl.rate_limit_info.remaining = 2000 
        
        await rl.acquire()
        
        # Check that sleep was called. The exact value has jitter, so we check if it was called.
        mock_sleep.assert_called()
        # The first call to time.time() is at the start of acquire(),
        # the second is for _last_request. The delay calculation uses the first one.
        # Expected delay is around 1.0 seconds.
        assert mock_sleep.call_args[0][0] > 0.5


async def test_acquire_updates_last_request_time():
    """Test that acquire() correctly updates the _last_request timestamp."""
    rl = RateLimiter()
    
    with patch('time.time', return_value=12345.0) as mock_time:
        # Patch sleep to make the test run instantly
        with patch('asyncio.sleep'):
            await rl.acquire()
            assert rl._last_request == 12345.0


## 5. Task Safety Test
# ---------------------

async def test_update_rate_limit_info_is_task_safe():
    """Ensure concurrent updates do not corrupt the RateLimiter's state."""
    rl = RateLimiter()
    num_tasks = 50
    
    async def worker(headers):
        # Add a small, random delay to increase the chance of race conditions if unlocked
        await asyncio.sleep(0.01 * random.random())
        await rl.update_rate_limit_info(headers)

    # Create many concurrent tasks
    all_headers = []
    for i in range(num_tasks):
        headers = {
            "x-ratelimit-limit": str(5000 + i),
            "x-ratelimit-remaining": str(4000 + i),
        }
        all_headers.append(headers)
    
    tasks = [asyncio.create_task(worker(h)) for h in all_headers]
    await asyncio.gather(*tasks)

    # The final state should be internally consistent, belonging to one of the updates.
    # If limit is 5000+i, remaining must be 4000+i.
    final_limit = rl.rate_limit_info.limit
    final_remaining = rl.rate_limit_info.remaining
    
    # Calculate what 'i' must have been based on the final limit
    i = final_limit - 5000
    expected_remaining = 4000 + i
    assert final_remaining == expected_remaining, "Inconsistent state suggests a race condition"