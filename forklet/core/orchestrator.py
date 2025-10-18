"""
Orchestrator for managing the complete download process 
with concurrency and error handling.
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
from datetime import datetime

from ..models import (
    DownloadRequest, DownloadResult, ProgressInfo, DownloadStatus,
    GitHubFile
)
from ..services import GitHubAPIService, DownloadService
from .filter import FilterEngine

from forklet.infrastructure.logger import logger



####
##      DOWNLOAD STATISTICS MODEL
#####
@dataclass
class DownloadStatistics:
    """Detailed statistics for download operations."""
    
    total_files: int = 0
    downloaded_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    total_bytes: int = 0
    cache_hits: int = 0
    api_calls: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds."""

        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def download_speed(self) -> float:
        """Calculate average download speed in bytes/second."""

        duration = self.duration_seconds
        if duration > 0 and self.total_bytes > 0:
            return self.total_bytes / duration
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""

        total_attempted = self.downloaded_files + self.failed_files
        if total_attempted > 0:
            return (self.downloaded_files / total_attempted) * 100.0
        return 0.0


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
        max_concurrent_downloads: int = 10
    ):
        self.github_service = github_service
        self.download_service = download_service
        self.max_concurrent_downloads = max_concurrent_downloads
        self._is_cancelled = False
        self._is_paused = False
        self._semaphore = asyncio.Semaphore(max_concurrent_downloads)
        
        # State tracking for control methods
        self._current_result: Optional[DownloadResult] = None
        self._active_tasks: List[asyncio.Task] = []
        self._pause_event = asyncio.Event()
        self._cancellation_event = asyncio.Event()
        self._resume_event = asyncio.Event()
        self._paused_files: List[str] = []
        self._completed_files: Set[str] = set()
        self._failed_files: Dict[str, str] = {}
    
    async def execute_download(self, request: DownloadRequest) -> DownloadResult:
        """
        Execute the complete download process asynchronously.
        
        Args:
            request: Download request configuration
            
        Returns:
            DownloadResult with comprehensive results
        """
        if self._is_cancelled:
            raise RuntimeError("Download orchestrator has been cancelled")
        
        logger.debug(
            "Starting async download for "
            f"{request.repository.display_name}@{request.git_ref}"
        )
        
        # Initialize statistics and progress
        stats = DownloadStatistics(start_time=datetime.now())
        progress = ProgressInfo(
            total_files=0, 
            downloaded_files=0, 
            total_bytes=0, 
            downloaded_bytes=0
        )
        
        try:
            # Get repository tree
            files = await self.github_service.get_repository_tree(
                request.repository.owner,
                request.repository.name,
                request.git_ref
            )
            stats.api_calls += 1
            
            # Filter files
            filter_engine = FilterEngine(request.filters)
            filter_result = filter_engine.filter_files(files)
            
            target_files = filter_result.included_files
            progress.total_files = len(target_files)
            progress.total_bytes = sum(file.size for file in target_files)
            
            logger.debug(
                f"Filtered {filter_result.filtered_files}/{filter_result.total_files} "
                "files for download"
            )

            # Create download result and set as current (so control operations can act)
            result = DownloadResult(
                request=request,
                status=DownloadStatus.IN_PROGRESS,
                progress=progress,
                started_at=datetime.now()
            )
            # Expose matched file paths for verbose reporting
            result.matched_files = [f.path for f in target_files]
            self._current_result = result

            # If dry-run is explicitly requested, prepare a summary and return without writing files
            if getattr(request, 'dry_run', None) is True:
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
                logger.info(f"Dry-run: {len(target_files)} files matched, {len(skipped)} would be skipped")
                return result

            # Prepare destination
            if request.create_destination:
                await self.download_service.ensure_directory(request.destination)
            
            # Reset state tracking
            self._completed_files.clear()
            self._failed_files.clear()
            self._paused_files.clear()
            
            # Download files concurrently with asyncio
            downloaded_files, failed_files = await self._download_files_concurrently(
                target_files, request, progress, stats
            )
            
            # Update result
            result.downloaded_files = downloaded_files
            result.failed_files = failed_files
            result.cache_hits = stats.cache_hits
            result.api_calls_made = stats.api_calls
    
            # Mark as completed
            stats.end_time = datetime.now()
            result.mark_completed()
            
            logger.debug(
                f"Download completed: {len(downloaded_files)} successful, "
                f"{len(failed_files)} failed, {stats.total_bytes} bytes"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            result = DownloadResult(
                request = request,
                status = DownloadStatus.FAILED,
                progress = progress,
                error_message = str(e),
                started_at = datetime.now(),
                completed_at = datetime.now()
            )
            
            return result
            
        finally:
            # Clean up state regardless of success or failure
            self.reset_state()
    
    async def _download_files_concurrently(
        self,
        files: List[GitHubFile],
        request: DownloadRequest,
        progress: ProgressInfo,
        stats: DownloadStatistics
    ) -> tuple[List[str], Dict[str, str]]:
        """
        Download files concurrently using asyncio.gather with semaphore.
        
        Args:
            files: List of files to download
            request: Download request
            progress: Progress tracker
            stats: Statistics tracker
            
        Returns:
            Tuple of (downloaded_files, failed_files)
        """
        downloaded_files = []
        failed_files = {}
        
        # Filter out already completed files if resuming
        remaining_files = [file for file in files if file.path not in self._completed_files]
        
        # Create download tasks with semaphore control
        tasks = [
            self._download_single_file_with_semaphore(file, request, progress, stats)
            for file in remaining_files
        ]
        
        # Store active tasks for cancellation
        self._active_tasks = tasks
        
        try:
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for file, result in zip(remaining_files, results):
                if self._cancellation_event.is_set():
                    if file.path not in self._completed_files and file.path not in failed_files:
                        self._paused_files.append(file.path)
                    break
                    
                if isinstance(result, Exception):
                    stats.failed_files += 1
                    failed_files[file.path] = str(result)
                    self._failed_files[file.path] = str(result)
                    logger.error(f"Failed to download {file.path}: {result}")
                elif result is not None:
                    downloaded_files.append(file.path)
                    self._completed_files.add(file.path)
                    stats.downloaded_files += 1
                    stats.total_bytes += result
                else:
                    stats.skipped_files += 1
            
            # Add previously completed files to downloaded_files
            downloaded_files.extend(self._completed_files)
            
        except asyncio.CancelledError:
            logger.info("Download operation was cancelled")
            # Ensure all tasks are properly cancelled
            for task in self._active_tasks:
                if not task.done():
                    task.cancel()
            raise
        
        finally:
            # Clear active tasks
            self._active_tasks.clear()
        
        return downloaded_files, failed_files
    
    async def _download_single_file_with_semaphore(
        self,
        file: GitHubFile,
        request: DownloadRequest,
        progress: ProgressInfo,
        stats: DownloadStatistics
    ) -> Optional[int]:
        """
        Download a single file with semaphore control.
        
        Args:
            file: File to download
            request: Download request
            progress: Progress tracker
            stats: Statistics tracker
            
        Returns:
            Number of bytes downloaded, or None if skipped
        """
        async with self._semaphore:
            return await self._download_single_file(file, request, progress, stats)
    
    async def _download_single_file(
        self,
        file: GitHubFile,
        request: DownloadRequest,
        progress: ProgressInfo,
        stats: DownloadStatistics
    ) -> Optional[int]:
        """
        Download a single file with comprehensive error handling.
        
        Args:
            file: File to download
            request: Download request
            progress: Progress tracker
            stats: Statistics tracker
            
        Returns:
            Number of bytes downloaded, or None if skipped
            
        Raises:
            Exception: If download fails
        """
        
        # Check for cancellation
        if self._cancellation_event.is_set():
            return None
            
        # Check for pause before starting
        await self._wait_for_resume()
        
        if self._cancellation_event.is_set():
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
                return None
            
            # Download file content
            content = await self.github_service.get_file_content(file.download_url)
            stats.api_calls += 1
            
            # Check again for pause after API call
            await self._wait_for_resume()
            
            if self._cancellation_event.is_set():
                return None
            
            # Save content to file
            bytes_written = await self.download_service.save_content(
                content, 
                target_path,
                show_progress = request.show_progress_bars
            )
            
            # Update progress
            progress.update_file_progress(bytes_written, file.path)
            progress.complete_file()
            
            logger.debug(f"Downloaded {file.path} ({bytes_written} bytes)")
            return bytes_written
            
        except Exception as e:
            logger.error(f"Error downloading {file.path}: {e}")
            raise
    
    async def _wait_for_resume(self) -> None:
        """
        Wait for resume event if paused, or return immediately if not paused.
        This method handles the pause/resume mechanism.
        """
        if self._is_paused and not self._cancellation_event.is_set():
            logger.debug("Download operation is paused, waiting for resume...")
            await self._pause_event.wait()
            logger.debug("Download operation resumed")
    
    def cancel(self) -> Optional[DownloadResult]:
        """
        Cancel the current download operation.
        
        Returns:
            Current DownloadResult marked as cancelled, or None if no active download
        """
        if self._current_result is None:
            logger.warning("No active download to cancel")
            return None
            
        self._is_cancelled = True
        
        # Signal cancellation to all pending tasks
        self._cancellation_event.set()
        
        # Cancel all active tasks
        for task in self._active_tasks:
            if not task.done():
                task.cancel()
        
        # Update the current result status
        self._current_result.status = DownloadStatus.CANCELLED
        self._current_result.completed_at = datetime.now()
        
        logger.info("Download cancelled by user")
        return self._current_result
    
    async def pause(self) -> Optional[DownloadResult]:
        """
        Pause the current download operation.
        
        Returns:
            Current DownloadResult marked as paused, or None if no active download
        """
        if self._current_result is None:
            logger.warning("No active download to pause")
            return None
            
        if self._is_paused:
            logger.warning("Download is already paused")
            return self._current_result
            
        self._is_paused = True
        
        # Clear the pause event to block further downloads
        self._pause_event.clear()
        
        # Update the current result status
        self._current_result.status = DownloadStatus.PAUSED
        
        logger.info("Download paused")
        return self._current_result
    
    async def resume(self) -> Optional[DownloadResult]:
        """
        Resume a paused download operation.
        
        Returns:
            Current DownloadResult marked as resuming, or None if no paused download
        """
        if self._current_result is None:
            logger.warning("No active download to resume")
            return None
            
        if not self._is_paused:
            logger.warning("Download is not paused")
            return self._current_result
            
        self._is_paused = False
        
        # Reset the pause event to allow downloads to continue
        self._pause_event.set()
        
        # Update the current result status
        self._current_result.status = DownloadStatus.IN_PROGRESS
        
        logger.info("Download resumed")
        return self._current_result
    
    def get_current_progress(self) -> Optional[ProgressInfo]:
        """
        Get current progress information.
        
        Returns:
            Current ProgressInfo if a download is in progress, None otherwise
        """
        if self._current_result is None:
            return None
            
        # Return the current progress with updated statistics
        progress = self._current_result.progress
        
        # Update progress with current state if we have tracking data
        if hasattr(self, '_completed_files'):
            progress.downloaded_files = len(self._completed_files)
        
        # Create a progress info snapshot with current state
        current_progress = ProgressInfo(
            total_files=progress.total_files,
            downloaded_files=progress.downloaded_files,
            total_bytes=progress.total_bytes,
            downloaded_bytes=progress.downloaded_bytes,
            current_file=progress.current_file
        )
        
        return current_progress
    
    def reset_state(self) -> None:
        """
        Reset the orchestrator state after a download completes.
        This should be called to clean up state after successful completion or failure.
        """
        self._current_result = None
        self._active_tasks.clear()
        self._is_cancelled = False
        self._is_paused = False
        self._paused_files.clear()
        self._completed_files.clear()
        self._failed_files.clear()
        
        # Reset events
        self._cancellation_event.clear()
        self._pause_event.set()  # Set to allow downloads initially
        self._resume_event.clear()
