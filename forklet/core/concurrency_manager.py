"""
Concurrency manager for handling semaphore-controlled async operations.
"""

import asyncio
from typing import List, Optional, Tuple, Callable, Any, TypeVar
from dataclasses import dataclass, field
from datetime import datetime

from forklet.infrastructure.logger import logger

T = TypeVar("T")


@dataclass
class ConcurrencyStats:
    """Statistics for concurrency operations."""

    started_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    start_time: Optional[datetime] = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class ConcurrencyManager:
    """
    Manages concurrent async operations with semaphore control.

    Handles task creation, execution with semaphore limits,
    and provides statistics and control mechanisms.
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._stats = ConcurrencyStats()
        self._active_tasks: List[asyncio.Task] = []
        self._is_cancelled = False
        self._cancellation_event = asyncio.Event()

    async def execute_with_concurrency(
        self,
        items: List[Any],
        processor: Callable[[Any], Any],
        *,
        return_exceptions: bool = True,
    ) -> Tuple[List[Any], List[Exception]]:
        """
        Process items concurrently with semaphore control.

        Args:
            items: List of items to process
            processor: Async function to process each item
            return_exceptions: Whether to return exceptions or raise them

        Returns:
            Tuple of (results, exceptions) where results contains successful outputs
            and exceptions contains failed operations (if return_exceptions=True)
        """
        if self._is_cancelled:
            raise RuntimeError("Concurrency manager has been cancelled")

        self._stats.start_time = datetime.now()
        self._stats.started_tasks = len(items)
        self._active_tasks.clear()

        # Create tasks with semaphore control
        tasks = [self._process_with_semaphore(item, processor) for item in items]

        # Store active tasks for potential cancellation
        self._active_tasks = tasks

        try:
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)

            # Separate successful results from exceptions
            successful_results = []
            exceptions = []

            for item, result in zip(items, results):
                if isinstance(result, Exception):
                    self._stats.failed_tasks += 1
                    exceptions.append(result)
                else:
                    self._stats.completed_tasks += 1
                    successful_results.append(result)

            return successful_results, exceptions

        except asyncio.CancelledError:
            logger.info("Concurrent operation was cancelled")
            # Ensure all tasks are properly cancelled
            for task in self._active_tasks:
                if not task.done():
                    task.cancel()
            raise
        finally:
            # Clear active tasks and update stats
            self._active_tasks.clear()
            self._stats.end_time = datetime.now()

    async def _process_with_semaphore(
        self, item: Any, processor: Callable[[Any], Any]
    ) -> Any:
        """Process a single item with semaphore control."""
        async with self._semaphore:
            # Check for cancellation before processing
            if self._cancellation_event.is_set():
                return None

            try:
                return await processor(item)
            except Exception:
                # Re-raise to be handled by gather
                raise

    def cancel(self) -> None:
        """Cancel all pending operations."""
        if not self._active_tasks:
            return

        self._is_cancelled = True
        self._cancellation_event.set()

        # Cancel all active tasks
        for task in self._active_tasks:
            if not task.done():
                task.cancel()

        logger.info("Concurrency manager cancelled")

    def get_stats(self) -> ConcurrencyStats:
        """Get current concurrency statistics."""
        return self._stats

    def is_busy(self) -> bool:
        """Check if there are active tasks."""
        return len(self._active_tasks) > 0
