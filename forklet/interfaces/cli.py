# src/github_downloader/interfaces/cli.py
"""
Command-line interface for Forklet GitHub Repository Downloader.
"""

import click
import logging
import sys
from pathlib import Path
from typing import List, Optional

from forklet.core import DownloadOrchestrator
from forklet.services import GitHubAPIService, DownloadService
from forklet.infrastructure import (
    RateLimiter, RetryManager, DownloadError, 
    RateLimitError, AuthenticationError, RepositoryNotFoundError
)
from forklet.models import (
    DownloadRequest, DownloadStrategy, FilterCriteria,
    DownloadResult
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('forklet.log')
    ]
)

logger = logging.getLogger(__name__)


class ForkletCLI:
    """Main CLI application class."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.retry_manager = RetryManager()
        self.github_service: Optional[GitHubAPIService] = None
        self.download_service: Optional[DownloadService] = None
        self.orchestrator: Optional[DownloadOrchestrator] = None
    
    def initialize_services(
        self, auth_token: Optional[str] = None
    ) -> None:
        """Initialize all services with optional authentication."""

        self.github_service = GitHubAPIService(
            self.rate_limiter, self.retry_manager, auth_token
        )
        self.download_service = DownloadService(self.retry_manager)
        self.orchestrator = DownloadOrchestrator(
            self.github_service, self.download_service
        )
    
    def parse_repository_string(self, repo_str: str) -> tuple[str, str]:
        """
        Parse repository string in format owner/repo.
        
        Args:
            repo_str: Repository string
            
        Returns:
            Tuple of (owner, repo)
            
        Raises:
            click.BadParameter: If format is invalid
        """

        if '/' not in repo_str:
            raise click.BadParameter(
                "Repository must be in format 'owner/repo'"
            )
        
        parts = repo_str.split('/')
        if len(parts) != 2:
            raise click.BadParameter(
                "Repository must be in format 'owner/repo'"
            )
        
        return parts[0], parts[1]
    
    def create_filter_criteria(
        self,
        include: List[str],
        exclude: List[str],
        max_size: Optional[int],
        min_size: Optional[int],
        extensions: List[str],
        exclude_extensions: List[str],
        include_hidden: bool,
        include_binary: bool,
        target_paths: List[str]
    ) -> FilterCriteria:
        """
        Create filter criteria from CLI options.
        
        Args:
            include: Include patterns
            exclude: Exclude patterns
            max_size: Maximum file size
            min_size: Minimum file size
            extensions: Allowed extensions
            exclude_extensions: Excluded extensions
            include_hidden: Include hidden files
            include_binary: Include binary files
            target_paths: Specific paths to download
            
        Returns:
            FilterCriteria object
        """

        return FilterCriteria(
            include_patterns = include,
            exclude_patterns = exclude,
            max_file_size = max_size,
            min_file_size = min_size,
            file_extensions = set(extensions),
            excluded_extensions = set(exclude_extensions),
            include_hidden = include_hidden,
            include_binary = include_binary,
            target_paths = target_paths
        )
    
    def execute_download(
        self,
        repository: str,
        destination: str,
        ref: str,
        filters: FilterCriteria,
        strategy: DownloadStrategy,
        token: Optional[str],
        concurrent: int,
        overwrite: bool
    ) -> None:
        """
        Execute the download operation.
        
        Args:
            repository: Repository string (owner/repo)
            destination: Destination directory
            ref: Git reference
            filters: Filter criteria
            strategy: Download strategy
            token: Authentication token
            concurrent: Concurrent downloads
            overwrite: Overwrite existing files
        """

        try:
            # Initialize services
            self.initialize_services(token)
            
            # Parse repository
            owner, repo_name = self.parse_repository_string(repository)
            
            # Get repository info
            click.echo(f"📦 Fetching repository information for {owner}/{repo_name}...")
            repo_info = self.github_service.get_repository_info(owner, repo_name)
            
            # Resolve Git reference
            click.echo(f"🔍 Resolving reference '{ref}'...")
            git_ref = self.github_service.resolve_reference(owner, repo_name, ref)
            
            # Create download request
            request = DownloadRequest(
                repository = repo_info,
                git_ref = git_ref,
                destination = Path(destination),
                strategy = strategy,
                filters = filters,
                token = token,
                max_concurrent_downloads = concurrent,
                overwrite_existing = overwrite
            )
            
            # Execute download
            click.echo(f"🚀 Starting download with {concurrent} concurrent workers...")
            result = self.orchestrator.execute_download(request)
            
            # Display results
            self.display_results(result)
            
        except (
            RateLimitError, AuthenticationError, 
            RepositoryNotFoundError, DownloadError
        ) as e:
            click.echo(f"❌ Error: {e}", err=True)
            sys.exit(1)

        except Exception as e:
            click.echo(f"💥 Unexpected error: {e}", err=True)
            logger.exception("Unexpected error in download operation")
            sys.exit(1)
    
    def display_results(self, result: DownloadResult) -> None:
        """
        Display download results in a user-friendly format.
        
        Args:
            result: Download result
        """

        if hasattr(result, 'is_successful') and result.is_successful:
            click.echo("✅ Download completed successfully!")
            click.echo(f"   📁 Files: {len(result.downloaded_files)} downloaded")
            click.echo(f"   💾 Size: {result.progress.downloaded_bytes} bytes")
            # click.echo(f"   ⚡ Speed: {result.average_speed:.2f} bytes/sec")
            
            if result.skipped_files:
                click.echo(f"   ⏭️  Skipped: {len(result.skipped_files)} files")
                
        elif hasattr(result, 'failed_files') and result.failed_files:
            click.echo("⚠️  Download completed with errors:")
            click.echo(f"   ✅ Successful: {len(result.downloaded_files)}")
            click.echo(f"   ❌ Failed: {len(result.failed_files)}")
            
            # Show first few errors
            for i, (filename, error) in enumerate(list(result.failed_files.items())[:3]):
                click.echo(f"      {filename}: {error}")
            if len(result.failed_files) > 3:
                click.echo(f"      ... and {len(result.failed_files) - 3} more errors")
        
        else:
            click.echo("❌ Download failed completely")
