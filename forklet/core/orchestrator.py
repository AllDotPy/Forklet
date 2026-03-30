"""
Orchestrator for managing the complete download process
with concurrency and error handling.
"""

import asyncio
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from ..models import (
    DownloadRequest,
    DownloadResult,
    ProgressInfo,
    DownloadStatus,
    GitHubFile,
    VerificationMethod,
)
from ..services import GitHubAPIService, DownloadService
from .filter import FilterEngine
from .concurrency_manager import ConcurrencyManager
from .progress_tracker import ProgressTracker
from .state_controller import StateController

from forklet.infrastructure.logger import logger


####
##      DOWNLOAD ORCHESTRATOR
#####
class DownloadOrchestrator:
    """
    Orchestrates the complete download process with concurrency,
    error handling, and progress tracking.
    """

    def __init__(
        self,
        github_service: GitHubAPIService,
        download_service: DownloadService,
        max_concurrent_downloads: int = 10,
    ):
        self.github_service = github_service
        self.download_service = download_service
        self._max_concurrent_downloads = max_concurrent_downloads

        # Initialize extracted components
        self.concurrency_manager = ConcurrencyManager(max_concurrent_downloads)
        self.progress_tracker = ProgressTracker()
        self.state_controller = StateController()

        # Backwards compatibility attributes (for existing tests)
        self._semaphore = self.concurrency_manager._semaphore
        self._is_cancelled = self.state_controller.is_cancelled
        self._is_paused = self.state_controller.is_paused
        self._current_result = None
        self._active_tasks = self.concurrency_manager._active_tasks

        # Set up rate limit callback to adjust concurrency based on API rate limit status
        self.github_service.rate_limiter.set_rate_limit_callback(
            self._on_rate_limit_update
        )

    @property
    def is_cancelled(self) -> bool:
        """Check if the orchestrator is cancelled (backwards compatibility)."""
        return self._is_cancelled

    @property
    def is_paused(self) -> bool:
        """Check if the orchestrator is paused (backwards compatibility)."""
        return self._is_paused

    @property
    def max_concurrent_downloads(self) -> int:
        """Get the maximum number of concurrent downloads."""
        return self._max_concurrent_downloads

    async def execute_download(self, request: DownloadRequest) -> DownloadResult:
        """
        Execute the complete download process asynchronously.

        Args:
            request: Download request configuration

        Returns:
            DownloadResult with comprehensive results
        """
        if self.state_controller.is_cancelled:
            raise RuntimeError("Download orchestrator has been cancelled")

        logger.debug(
            "Starting async download for "
            f"{request.repository.display_name}@{request.git_ref}"
        )

        # Initialize statistics and progress
        try:
            # Get repository tree
            files = await self.github_service.get_repository_tree(
                request.repository.owner, request.repository.name, request.git_ref
            )
            stats = type("obj", (object,), {"api_calls": 0})()  # Simple stats object
            stats.api_calls += 1

            # Filter files
            filter_engine = FilterEngine(request.filters)
            filter_result = filter_engine.filter_files(files)

            target_files = filter_result.included_files

            # Reset progress tracker for this download (we are about to set new totals)
            self.progress_tracker.reset()

            # Set up progress tracking
            self.progress_tracker.set_total_files(len(target_files))
            self.progress_tracker.set_total_bytes(
                sum(file.size for file in target_files)
            )
            self.progress_tracker.matched_files = [f.path for f in target_files]

            logger.debug(
                f"Filtered {filter_result.filtered_files}/{filter_result.total_files} "
                "files for download"
            )

            # Create download result and set as current (so control operations can act)
            result = DownloadResult(
                request=request,
                status=DownloadStatus.IN_PROGRESS,
                progress=self.progress_tracker.get_progress_snapshot(),
                started_at=datetime.now(),
            )
            self.state_controller.set_current_result(result)
            # Update backwards compatibility attribute
            self._current_result = result

            # If dry-run is explicitly requested, prepare a summary and return without writing files
            if getattr(request, "dry_run", None) is True:
                # Determine which files would be skipped due to existing local files
                skipped = []
                for f in target_files:
                    if request.preserve_structure:
                        target_path = request.destination / f.path
                    else:
                        target_path = request.destination / Path(f.path).name
                    if target_path.exists() and not request.overwrite_existing:
                        skipped.append(f.path)

                # Update and return the result summarizing what would happen
                result.status = DownloadStatus.COMPLETED
                result.downloaded_files = []
                result.skipped_files = skipped
                result.failed_files = {}
                result.completed_at = datetime.now()
                # matched_files already set above; keep it for verbose output
                logger.info(
                    f"Dry-run: {len(target_files)} files matched, {len(skipped)} would be skipped"
                )

                # Clean up state
                self.state_controller.clear_current_result()
                self._current_result = None
                self.progress_tracker.reset()
                self.state_controller.reset()
                self.concurrency_manager = ConcurrencyManager(
                    self._max_concurrent_downloads
                )
                return result

            # Prepare destination
            if request.create_destination:
                await self.download_service.ensure_directory(request.destination)

            # Reset state tracking in our components
            self.progress_tracker.reset()
            self.state_controller.reset_tracking()

            # Update backwards compatibility attributes after reset
            self._is_cancelled = self.state_controller.is_cancelled
            self._is_paused = self.state_controller.is_paused

            # Download files concurrently with our concurrency manager
            downloaded_files, failed_files = await self._download_files_concurrently(
                target_files, request
            )

            # Get skipped count from progress tracker
            _, _, skipped_count = self.progress_tracker.get_results()

            # Update result
            result.downloaded_files = downloaded_files
            result.failed_files = failed_files
            result.skipped_files = [
                None
            ] * skipped_count  # Placeholder for compatibility
            result.cache_hits = 0  # TODO: Implement cache hits tracking
            result.api_calls_made = stats.api_calls  # Use actual API calls count

            # Mark as completed
            result.mark_completed()

            logger.debug(
                f"Download completed: {len(downloaded_files)} successful, "
                f"{len(failed_files)} failed"
            )

            return result

        except Exception as e:
            logger.error(f"Download failed: {e}")
            result = DownloadResult(
                request=request,
                status=DownloadStatus.FAILED,
                progress=self.progress_tracker.get_progress_snapshot(),
                error_message=str(e),
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

            return result
        finally:
            # Clean up state regardless of success or failure
            self.state_controller.clear_current_result()
            self._current_result = None
            self.progress_tracker.reset()
            self.state_controller.reset()
            self.concurrency_manager = ConcurrencyManager(
                self._max_concurrent_downloads
            )

    async def _download_files_concurrently(
        self, files: List[GitHubFile], request: DownloadRequest
    ) -> tuple[List[str], Dict[str, str]]:
        """
        Download files concurrently using asyncio.gather with semaphore.

        Args:
            files: List of files to download
            request: Download request

        Returns:
            Tuple of (downloaded_files, failed_files)
        """

        # Define the processor function for a single file
        async def process_file(file: GitHubFile) -> Optional[int]:
            return await self._download_single_file(file, request)

        # Execute with concurrency manager
        (
            downloaded_bytes_list,
            exceptions,
        ) = await self.concurrency_manager.execute_with_concurrency(
            files, process_file, return_exceptions=True
        )

        # Process results
        downloaded_files = []
        failed_files = {}

        for file, result_or_exception in zip(
            files, downloaded_bytes_list + [None] * len(exceptions)
        ):
            # Handle exceptions from the gather
            if isinstance(result_or_exception, Exception):
                failed_files[file.path] = str(result_or_exception)
                logger.error(f"Failed to download {file.path}: {result_or_exception}")
                self.progress_tracker.add_failed_file(
                    file.path, str(result_or_exception)
                )
            elif result_or_exception is not None:
                # Successful download
                downloaded_files.append(file.path)
                self.progress_tracker.add_completed_file(file.path)
                logger.debug(f"Downloaded {file.path} ({result_or_exception} bytes)")
            else:
                # Skipped file (None result)
                self.progress_tracker.add_skipped_file()

        # Get the final results from progress tracker
        completed_files, failed_files_dict, skipped_count = (
            self.progress_tracker.get_results()
        )

        # Ensure failed files from exceptions are included
        failed_files.update(failed_files_dict)

        return downloaded_files, failed_files

    async def _download_single_file(
        self, file: GitHubFile, request: DownloadRequest
    ) -> Optional[int]:
        """
        Download a single file with comprehensive error handling.

        Args:
            file: File to download
            request: Download request

        Returns:
            Number of bytes downloaded, or None if skipped

        Raises:
            Exception: If download fails
        """

        # Check for cancellation via state controller
        if self.state_controller.is_cancelled:
            return None

        # Check for pause before starting
        await self.state_controller.wait_for_resume()

        if self.state_controller.is_cancelled:
            return None

        try:
            # Determine target path
            if request.preserve_structure:
                target_path = request.destination / file.path
            else:
                target_path = request.destination / Path(file.path).name

            # Check if file already exists
            if target_path.exists() and not request.overwrite_existing:
                logger.debug(f"Skipping existing file: {file.path}")
                self.progress_tracker.add_skipped_file()
                return None

            # Determine if we should stream based on file size
            should_stream = file.size > request.stream_threshold
            # Download file content (potentially as a stream for large files)
            content = await self.github_service.get_file_content(
                file.download_url, stream=should_stream
            )

            # Check again for pause after API call
            await self.state_controller.wait_for_resume()

            if self.state_controller.is_cancelled:
                return None

            # Save content to file
            bytes_written = await self.download_service.save_content(
                content,
                target_path,
                show_progress=request.show_progress_bars,
                is_stream=should_stream,
            )

            # Update progress
            self.progress_tracker.update_file_progress(bytes_written, file.path)
            self.progress_tracker.complete_file()

            # Verify integrity if requested
            if (
                request.verify_integrity
                and request.verification_method != VerificationMethod.NONE
            ):
                verified = False
                try:
                    if request.verification_method == VerificationMethod.GIT_BLOB_SHA1:
                        # Verify using Git blob SHA1
                        verified = await self._verify_git_blob_sha1(
                            target_path, file.sha
                        )
                    elif request.verification_method == VerificationMethod.SIZE:
                        # Verify using file size
                        actual_size = await asyncio.to_thread(
                            lambda: target_path.stat().st_size
                        )
                        verified = actual_size == file.size
                    # Add other methods as needed
                except Exception as e:
                    logger.warning(
                        f"Integrity verification failed for {file.path}: {e}"
                    )
                    verified = False

                if verified:
                    self.progress_tracker.verified_files.append(file.path)
                    logger.debug(f"Integrity verified for {file.path}")
                else:
                    self.progress_tracker.verification_failures[file.path] = (
                        "Integrity verification failed"
                    )
                    logger.warning(f"Integrity verification failed for {file.path}")
                    # Treat verification failure as a failure? For now, we'll still return the bytes but track it.
                    # Optionally we could delete the file and return None to trigger retry.

            logger.debug(f"Downloaded {file.path} ({bytes_written} bytes)")
            return bytes_written

        except Exception as e:
            logger.error(f"Error downloading {file.path}: {e}")
            self.progress_tracker.add_failed_file(file.path, str(e))
            raise

    async def _verify_git_blob_sha1(self, file_path: Path, expected_sha: str) -> bool:
        """
        Verify a file's SHA-1 hash matches the expected Git blob SHA-1.

        Git blob SHA-1 is computed as: SHA1("blob " + <size> + "\0" + <content>)

        Args:
            file_path: Path to the file to verify
            expected_sha: Expected SHA-1 hash

        Returns:
            True if verification passes, False otherwise
        """
        try:
            # Read file content
            content = await asyncio.to_thread(lambda: file_path.read_bytes())

            # Create Git blob header: "blob <size>\0"
            header = f"blob {len(content)}\0".encode("utf-8")

            # Calculate SHA1 of header + content
            sha1_hash = hashlib.sha1(header + content).hexdigest()

            return sha1_hash == expected_sha
        except Exception as e:
            logger.debug(f"Git blob SHA1 verification failed for {file_path}: {e}")
            return False

    # Delegate methods to state controller for external control
    def cancel(self) -> Optional[DownloadResult]:
        """
        Cancel the current download operation.

        Returns:
            Current DownloadResult marked as cancelled, or None if no active download
        """
        # Check if there's an active download to cancel
        if self.state_controller._current_result is None:
            logger.warning("No active download to cancel")
            return None

        # Get result from state controller
        result = self.state_controller.cancel()
        if result:
            # Also cancel any ongoing concurrency operations
            self.concurrency_manager.cancel()
            logger.info("Download cancelled by user")
            # Update backwards compatibility attribute
            self._is_cancelled = self.state_controller.is_cancelled
        return result

    async def pause(self) -> Optional[DownloadResult]:
        """
        Pause the current download operation.

        Returns:
            Current DownloadResult marked as paused, or None if no active download
        """
        result = self.state_controller.pause()
        if result:
            # Update the progress in the result
            result.progress = self.progress_tracker.get_progress_snapshot()
            # Update backwards compatibility attribute
            self._is_paused = self.state_controller.is_paused
        return result

    async def resume(self) -> Optional[DownloadResult]:
        """
        Resume a paused download operation.

        Returns:
            Current DownloadResult marked as resuming, or None if no paused download
        """
        result = self.state_controller.resume()
        if result:
            # Update the progress in the result
            result.progress = self.progress_tracker.get_progress_snapshot()
            # Update backwards compatibility attribute
            self._is_paused = self.state_controller.is_paused
        return result

    def get_current_progress(self) -> Optional[ProgressInfo]:
        """
        Get current progress information.

        Returns:
            Current ProgressInfo if a download is in progress, None otherwise
        """
        if self.state_controller.current_result is None:
            return None

        # Return the current progress with updated state from our trackers
        progress = self.progress_tracker.get_progress_snapshot()

        # Update completed files count from our tracking (more accurate)
        progress.downloaded_files = len(self.progress_tracker._completed_files)

        return progress

    def reset_state(self) -> None:
        """
        Reset the orchestrator state after a download completes.
        This should be called to clean up state after successful completion or failure.
        Maintains backwards compatibility with existing tests.
        """
        # Reset our component states
        self.concurrency_manager = ConcurrencyManager(self._max_concurrent_downloads)
        self.progress_tracker.reset()
        self.state_controller.reset()

        # Reset backwards compatibility attributes
        self._semaphore = self.concurrency_manager._semaphore
        self._is_cancelled = self.state_controller.is_cancelled
        self._is_paused = self.state_controller.is_paused
        self._current_result = None
        self._active_tasks = self.concurrency_manager._active_tasks

    def _on_rate_limit_update(self, rate_limit_info: RateLimitInfo) -> None:
        """
        Adjust download concurrency based on GitHub API rate limit status.

        This is called by the rate limiter when rate limit information is updated.
        It dynamically adjusts the concurrency level to stay within rate limits.
        """
        # Calculate a safe concurrency level based on remaining rate limit
        # We want to leave enough buffer for other API calls (repo info, etc.)
        # Assume we need ~10 API calls per download operation (simplified)
        api_calls_per_download = 10

        if rate_limit_info.remaining < api_calls_per_download * 2:
            # Very low rate limit - reduce concurrency significantly
            new_max_concurrent = max(
                1, rate_limit_info.remaining // (api_calls_per_download * 2)
            )
        elif rate_limit_info.remaining < api_calls_per_download * 10:
            # Moderate rate limit - reduce concurrency somewhat
            new_max_concurrent = max(
                1, rate_limit_info.remaining // (api_calls_per_download * 2)
            )
        else:
            # Plenty of rate limit - use configured maximum
            new_max_concurrent = self._max_concurrent_downloads

        # Apply the new concurrency level if it's different
        if new_max_concurrent != self.concurrency_manager.max_concurrent:
            logger.debug(
                f"Adjusting download concurrency from {self.concurrency_manager.max_concurrent} "
                f"to {new_max_concurrent} based on rate limit "
                f"({rate_limit_info.remaining}/{rate_limit_info.limit} remaining)"
            )
            self.concurrency_manager.update_max_concurrent(new_max_concurrent)
