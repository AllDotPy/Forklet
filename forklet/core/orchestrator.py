"""
Orchestrator for managing the complete download process 
with concurrency and error handling.
"""

import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass
from datetime import datetime

from ..models import (
    DownloadRequest, DownloadResult, ProgressInfo, DownloadStatus,
    FileDownloadInfo, GitHubFile
)
from ..services import GitHubAPIService, DownloadService
from .filter import FilterEngine, FilterResult


logger = logging.getLogger(__name__)


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
        max_workers: int = 10
    ):
        self.github_service = github_service
        self.download_service = download_service
        self.max_workers = max_workers
        self._is_cancelled = False
    
    def execute_download(self, request: DownloadRequest) -> DownloadResult:
        """
        Execute the complete download process.
        
        Args:
            request: Download request configuration
            
        Returns:
            DownloadResult with comprehensive results
        """

        if self._is_cancelled:
            raise RuntimeError(
                "Download orchestrator has been cancelled"
            )
        
        logger.info(f"Starting download for {request.repository.display_name}@{request.git_ref}")
        
        # Initialize statistics and progress
        stats = DownloadStatistics(start_time=datetime.now())
        progress = ProgressInfo(
            total_files = 0, 
            downloaded_files = 0, 
            total_bytes = 0, 
            downloaded_bytes = 0
        )
        
        try:
            # Get repository tree
            files = self.github_service.get_repository_tree(
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
            
            logger.info(
                f"Filtered {filter_result.filtered_files}/{filter_result.total_files} "
                "files for download"
            )
            
            # Prepare destination
            if request.create_destination:
                self.download_service.ensure_directory(request.destination)
            
            # Create download result
            result = DownloadResult(
                request = request,
                status = DownloadStatus.IN_PROGRESS,
                progress = progress,
                started_at = datetime.now()
            )
            
            # Download files concurrently
            downloaded_files, failed_files = self._download_files_concurrently(
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
            
            logger.info(
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
    
    def _download_files_concurrently(
        self,
        files: List[GitHubFile],
        request: DownloadRequest,
        progress: ProgressInfo,
        stats: DownloadStatistics
    ) -> tuple[List[str], Dict[str, str]]:
        """
        Download files concurrently with thread pool.
        
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
        
        with ThreadPoolExecutor(
            max_workers = request.max_concurrent_downloads
        ) as executor:
            # Submit all download tasks
            future_to_file = {
                executor.submit(
                    self._download_single_file,
                    file, request, progress, stats
                ): file for file in files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                
                try:
                    result = future.result()
                    if result:
                        downloaded_files.append(file.path)
                        stats.downloaded_files += 1
                        stats.total_bytes += result
                    else:
                        stats.skipped_files += 1
                        
                except Exception as e:
                    stats.failed_files += 1
                    failed_files[file.path] = str(e)
                    logger.error(f"Failed to download {file.path}: {e}")
                
                # Check for cancellation
                if self._is_cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
        
        return downloaded_files, failed_files
    
    def _download_single_file(
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

        if self._is_cancelled:
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
            content = self.github_service.get_file_content(file.download_url)
            stats.api_calls += 1
            
            # Save content to file
            bytes_written = self.download_service.save_content(content, target_path)
            
            # Update progress
            progress.update_file_progress(bytes_written, file.path)
            progress.complete_file()
            
            logger.debug(f"Downloaded {file.path} ({bytes_written} bytes)")
            return bytes_written
            
        except Exception as e:
            logger.error(f"Error downloading {file.path}: {e}")
            raise
    
    def cancel(self) -> None:
        """Cancel the current download operation."""

        self._is_cancelled = True
        logger.info("Download cancelled by user")
    
    def pause(self) -> None:
        """Pause the current download operation."""

        # Implementation would track state for resumable downloads
        logger.info("Download paused")
    
    def resume(self) -> None:
        """Resume a paused download operation."""

        # Implementation would resume from saved state
        logger.info("Download resumed")
    
    def get_current_progress(self) -> Optional[ProgressInfo]:
        """
        Get current progress information.
        
        Returns:
            Current ProgressInfo, or None if no download in progress
        """
        # Implementation would track progress state
        return None
    