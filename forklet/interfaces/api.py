# src/github_downloader/interfaces/api.py
"""
Python API for Forklet GitHub Repository Downloader.
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass

from forklet.core import DownloadOrchestrator
from forklet.services import GitHubAPIService, DownloadService
from forklet.infrastructure import RateLimiter, RetryManager
from forklet.models import (
    DownloadRequest, DownloadResult, DownloadStrategy, FilterCriteria,
    RepositoryInfo, GitReference, ProgressInfo
)


logger = logging.getLogger(__name__)


@dataclass
class DownloadConfig:
    """Configuration for API downloads."""
    
    max_concurrent_downloads: int = 5
    chunk_size: int = 8192
    timeout: int = 300
    overwrite_existing: bool = False
    preserve_structure: bool = True


class GitHubDownloader:
    """
    Main API class for programmatic access to Forklet functionality.
    
    Provides a clean, typed interface for downloading GitHub repository content.
    """
    
    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the downloader with optional authentication.
        
        Args:
            auth_token: GitHub personal access token for authentication
        """

        self.auth_token = auth_token
        self.rate_limiter = RateLimiter()
        self.retry_manager = RetryManager()
        
        self.github_service = GitHubAPIService(
            self.rate_limiter, self.retry_manager, auth_token
        )
        self.download_service = DownloadService(self.retry_manager)
        self.orchestrator = DownloadOrchestrator(
            self.github_service, self.download_service
        )
    
    def get_repository_info(self, owner: str, repo: str) -> RepositoryInfo:
        """
        Get information about a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            RepositoryInfo object
            
        Raises:
            RepositoryNotFoundError: If repository doesn't exist
            AuthenticationError: If authentication fails
        """

        return self.github_service.get_repository_info(owner, repo)
    
    def resolve_reference(self, owner: str, repo: str, ref: str) -> GitReference:
        """
        Resolve a Git reference to a specific commit SHA.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch name, tag name, or commit SHA
            
        Returns:
            GitReference object
            
        Raises:
            ValueError: If reference cannot be resolved
        """

        return self.github_service.resolve_reference(owner, repo, ref)
    
    def download(
        self,
        owner: str,
        repo: str,
        destination: Path,
        ref: str = "main",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        strategy: DownloadStrategy = DownloadStrategy.INDIVIDUAL,
        config: Optional[DownloadConfig] = None,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> DownloadResult:
        """
        Download files from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            destination: Local directory to save files
            ref: Branch, tag, or commit SHA
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            strategy: Download strategy to use
            config: Additional download configuration
            progress_callback: Callback for progress updates
            
        Returns:
            DownloadResult with comprehensive results
            
        Raises:
            DownloadError: If download fails
            RateLimitError: If rate limits are exceeded
            AuthenticationError: If authentication fails
        """

        try:
            # Get repository information
            repo_info = self.get_repository_info(owner, repo)
            git_ref = self.resolve_reference(owner, repo, ref)
            
            # Create filter criteria
            filters = FilterCriteria(
                include_patterns = include_patterns or [],
                exclude_patterns = exclude_patterns or []
            )
            
            # Create download request
            request = DownloadRequest(
                repository = repo_info,
                git_ref = git_ref,
                destination = destination,
                strategy = strategy,
                filters = filters,
                token = self.auth_token,
                max_concurrent_downloads = config.max_concurrent_downloads if config else 5,
                chunk_size = config.chunk_size if config else 8192,
                timeout = config.timeout if config else 300,
                overwrite_existing = config.overwrite_existing if config else False,
                preserve_structure = config.preserve_structure if config else True
            )
            
            # Execute download
            result = self.orchestrator.execute_download(request)
            
            return result
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
    
    def download_directory(
        self,
        owner: str,
        repo: str,
        directory_path: str,
        destination: Path,
        ref: str = "main",
        config: Optional[DownloadConfig] = None
    ) -> DownloadResult:
        """
        Download a specific directory from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            directory_path: Path to directory within repository
            destination: Local directory to save files
            ref: Branch, tag, or commit SHA
            config: Additional download configuration
            
        Returns:
            DownloadResult with comprehensive results
        """

        # Create filter criteria targeting specific directory
        filters = FilterCriteria(
            target_paths=[directory_path],
            include_patterns=[f"{directory_path}/**"]
        )
        
        return self.download(
            owner = owner,
            repo = repo,
            destination = destination,
            ref = ref,
            include_patterns = filters.include_patterns,
            exclude_patterns = filters.exclude_patterns,
            config = config
        )
    
    def download_file(
        self,
        owner: str,
        repo: str,
        file_path: str,
        destination: Path,
        ref: str = "main",
        config: Optional[DownloadConfig] = None
    ) -> DownloadResult:
        """
        Download a specific file from a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to file within repository
            destination: Local path to save file
            ref: Branch, tag, or commit SHA
            config: Additional download configuration
            
        Returns:
            DownloadResult with comprehensive results
        """

        # Create filter criteria targeting specific file
        filters = FilterCriteria(
            target_paths = [file_path],
            include_patterns = [file_path]
        )
        
        return self.download(
            owner = owner,
            repo = repo,
            destination = destination,
            ref = ref,
            include_patterns = filters.include_patterns,
            exclude_patterns = filters.exclude_patterns,
            config = config
        )
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current GitHub API rate limit information.
        
        Returns:
            Dictionary with rate limit details
        """

        return self.github_service.get_rate_limit_info()
    
    def cancel_current_download(self) -> None:
        """Cancel the currently running download operation."""

        self.orchestrator.cancel()
    
    def pause_current_download(self) -> None:
        """Pause the currently running download operation."""

        self.orchestrator.pause()
    
    def resume_current_download(self) -> None:
        """Resume a paused download operation."""

        self.orchestrator.resume()
    
    def get_download_progress(self) -> Optional[ProgressInfo]:
        """
        Get progress information for the current download.
        
        Returns:
            ProgressInfo object, or None if no download in progress
        """

        return self.orchestrator.get_current_progress()
