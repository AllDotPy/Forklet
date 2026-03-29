"""
State controller for managing download operation states (pause, resume, cancel).
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Set, Dict

from ..models import DownloadResult, DownloadStatus


@dataclass
class StateController:
    """
    Controls the state of a download operation (paused, cancelled, etc.).

    Manages events and flags for pausing, resuming, and cancelling operations.
    """

    # State flags
    _is_cancelled: bool = False
    _is_paused: bool = False

    # Backwards compatibility properties
    @property
    def is_cancelled(self) -> bool:
        """Backwards compatibility property."""
        return self._is_cancelled

    @property
    def is_paused(self) -> bool:
        """Backwards compatibility property."""
        return self._is_paused

    @property
    def current_result(self) -> Optional[DownloadResult]:
        """Get the current result reference."""
        return self._current_result

    # Events for async coordination
    _pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    _cancellation_event: asyncio.Event = field(default_factory=asyncio.Event)
    _resume_event: asyncio.Event = field(default_factory=asyncio.Event)

    # Tracking lists for state recovery
    _paused_files: List[str] = field(default_factory=list)
    _completed_files: Set[str] = field(default_factory=set)
    _failed_files: Dict[str, str] = field(default_factory=dict)

    # Reference to current result for state updates
    _current_result: Optional[DownloadResult] = None

    def __post_init__(self):
        """Initialize events to appropriate default states."""
        # Initially, pause event is set (allowing progress) and others are clear
        self._pause_event.set()

    def set_current_result(self, result: DownloadResult) -> None:
        """Set the current result reference for state updates."""
        self._current_result = result

    def clear_current_result(self) -> None:
        """Clear the current result reference."""
        self._current_result = None

    async def wait_for_resume(self) -> None:
        """
        Wait for resume event if paused, or return immediately if not paused.
        """
        if self._is_paused and not self._is_cancelled:
            await self._pause_event.wait()

    def cancel(self) -> Optional[DownloadResult]:
        """
        Cancel the current operation.

        Returns:
            Current DownloadResult marked as cancelled, or None if no active operation
        """
        if self._current_result is None:
            return None

        self._is_cancelled = True
        self._cancellation_event.set()

        # Update the current result status
        self._current_result.status = DownloadStatus.CANCELLED
        self._current_result.completed_at = datetime.now()

        return self._current_result

    def pause(self) -> Optional[DownloadResult]:
        """
        Pause the current operation.

        Returns:
            Current DownloadResult marked as paused, or None if no active operation
        """
        if self._current_result is None:
            return None

        if self._is_paused:
            return self._current_result

        self._is_paused = True
        self._pause_event.clear()  # Block further progress

        # Update the current result status
        self._current_result.status = DownloadStatus.PAUSED

        return self._current_result

    def resume(self) -> Optional[DownloadResult]:
        """
        Resume a paused operation.

        Returns:
            Current DownloadResult marked as resuming, or None if no paused operation
        """
        if self._current_result is None:
            return None

        if not self._is_paused:
            return self._current_result

        self._is_paused = False
        self._pause_event.set()  # Allow progress to continue

        # Update the current result status
        self._current_result.status = DownloadStatus.IN_PROGRESS

        return self._current_result

    def get_current_progress(self) -> Optional[dict]:
        """
        Get current state tracking information.

        Returns:
            Dictionary with current state tracking data, or None if no active operation
        """
        if self._current_result is None:
            return None

        return {
            "paused_files": list(self._paused_files),
            "completed_files": set(self._completed_files),
            "failed_files": dict(self._failed_files),
            "is_cancelled": self._is_cancelled,
            "is_paused": self._is_paused,
        }

    def update_tracking(
        self,
        completed_files: Optional[Set[str]] = None,
        failed_files: Optional[Dict[str, str]] = None,
        paused_files: Optional[List[str]] = None,
    ) -> None:
        """
        Update internal tracking sets/lists.

        Args:
            completed_files: Set of file paths to add to completed files
            failed_files: Dict of file paths to error messages to add to failed files
            paused_files: List of file paths to add to paused files
        """
        if completed_files:
            self._completed_files.update(completed_files)
        if failed_files:
            self._failed_files.update(failed_files)
        if paused_files:
            self._paused_files.extend(paused_files)

    def reset_tracking(self) -> None:
        """Reset tracking data and events, but keep the current result."""
        self._is_cancelled = False
        self._is_paused = False
        self._paused_files.clear()
        self._completed_files.clear()
        self._failed_files.clear()

        # Reset events
        self._cancellation_event.clear()
        self._pause_event.set()  # Set to allow progress initially
        self._resume_event.clear()

    def reset(self) -> None:
        """Reset all state to initial values."""
        self._is_cancelled = False
        self._is_paused = False
        self._paused_files.clear()
        self._completed_files.clear()
        self._failed_files.clear()
        self._current_result = None

        # Reset events
        self._cancellation_event.clear()
        self._pause_event.set()  # Set to allow progress initially
        self._resume_event.clear()
