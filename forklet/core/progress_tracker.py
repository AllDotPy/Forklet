"""
Progress tracker for managing download progress and statistics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Set, List

from ..models import ProgressInfo, DownloadResult


@dataclass
class ProgressTracker:
    """
    Tracks download progress and maintains related statistics.

    Separates progress tracking concerns from the main orchestrator logic.
    """

    # Core progress tracking
    progress: ProgressInfo = field(
        default_factory=lambda: ProgressInfo(
            total_files=0, downloaded_files=0, total_bytes=0, downloaded_bytes=0
        )
    )

    # File tracking sets
    _completed_files: Set[str] = field(default_factory=set)
    _failed_files: Dict[str, str] = field(default_factory=dict)
    _verified_files: Set[str] = field(default_factory=set)
    _verification_failures: Dict[str, str] = field(default_factory=dict)
    _skipped_count: int = 0

    # Matched files for reporting (populated by orchestrator)
    matched_files: List[str] = field(default_factory=list)

    def add_verified_file(self, file_path: str) -> None:
        """Add a successfully verified file to tracking."""
        self._verified_files.add(file_path)

    def add_verification_failure(self, file_path: str, error: str) -> None:
        """Add a verification failure to tracking."""
        self._verification_failures[file_path] = error

    def get_verification_results(self) -> tuple[List[str], Dict[str, str]]:
        """
        Get verification results.

        Returns:
            Tuple of (verified_files, verification_failures)
        """
        return list(self._verified_files), dict(self._verification_failures)

    def reset(self) -> None:
        """Reset all tracking state."""
        self.progress = ProgressInfo(
            total_files=0, downloaded_files=0, total_bytes=0, downloaded_bytes=0
        )
        self._completed_files.clear()
        self._failed_files.clear()
        self._verified_files.clear()
        self._verification_failures.clear()
        self._skipped_count = 0
        self.matched_files.clear()

    def update_file_progress(
        self, bytes_downloaded: int, current_file: Optional[str] = None
    ) -> None:
        """
        Update progress with bytes downloaded for current file.

        Args:
            bytes_downloaded: Number of bytes downloaded in this update
            current_file: Path of the file currently being processed
        """
        self.progress.downloaded_bytes += bytes_downloaded
        if current_file:
            self.progress.current_file = current_file

    def complete_file(self) -> None:
        """Mark one file as completed."""
        self.progress.downloaded_files += 1
        self.progress.current_file = None

    def add_completed_file(self, file_path: str) -> None:
        """Add a successfully downloaded file to tracking."""
        self._completed_files.add(file_path)
        self.complete_file()

    def add_failed_file(self, file_path: str, error: str) -> None:
        """Add a failed file to tracking."""
        self._failed_files[file_path] = error
        # Note: failed files don't increment downloaded_files count

    def add_skipped_file(self) -> None:
        """Increment skipped file count."""
        self._skipped_count += 1

    def set_total_files(self, total: int) -> None:
        """Set total number of files to process."""
        self.progress.total_files = total

    def set_total_bytes(self, total: int) -> None:
        """Set total number of bytes to process."""
        self.progress.total_bytes = total

    def get_progress_snapshot(self) -> ProgressInfo:
        """
        Get a current snapshot of progress.

        Returns:
            ProgressInfo with current state
        """
        # Update completed files count from our tracking
        progress_copy = ProgressInfo(
            total_files=self.progress.total_files,
            downloaded_files=len(self._completed_files),
            total_bytes=self.progress.total_bytes,
            downloaded_bytes=self.progress.downloaded_bytes,
            current_file=self.progress.current_file,
        )
        return progress_copy

    def get_results(self) -> tuple[List[str], Dict[str, str], int]:
        """
        Get final results from tracking.

        Returns:
            Tuple of (completed_files, failed_files, skipped_count)
        """
        return (
            list(self._completed_files),
            dict(self._failed_files),
            self._skipped_count,
        )

    def reset(self) -> None:
        """Reset all tracking state."""
        self.progress = ProgressInfo(
            total_files=0, downloaded_files=0, total_bytes=0, downloaded_bytes=0
        )
        self._completed_files.clear()
        self._failed_files.clear()
        self._skipped_count = 0
        self.matched_files.clear()
