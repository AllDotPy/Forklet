"""
Service for downloading files with progress tracking and error handling.
"""

import logging
from typing import Optional, Callable
from pathlib import Path
from dataclasses import dataclass

import httpx
from tqdm import tqdm

from ..infrastructure.retry_manager import RetryManager
from ..infrastructure.error_handler import (
    handle_api_error, retry_on_error, DownloadError
)
from ..models import ProgressInfo
from ..models.constants import USER_AGENT


logger = logging.getLogger(__name__)


####
##      DOWNLOAD CONFIGURATION MODEL
#####
@dataclass
class DownloadConfig:
    """Configuration for file downloads."""
    
    chunk_size: int = 8192
    timeout: int = 30
    max_retries: int = 3
    progress_callback: Optional[Callable[[int, int], None]] = None


####
##      DOWNLOAD SERVICE
#####
class DownloadService:
    """
    Service for downloading files with progress tracking, 
    retry logic, and error handling.
    """
    
    def __init__(self, retry_manager: Optional[RetryManager] = None):
        self.retry_manager = retry_manager or RetryManager()
        self.client = httpx.Client()
        self.client.headers.update({
            "User-Agent": USER_AGENT
        })
    
    @retry_on_error(max_retries=3)
    @handle_api_error
    def download_file(
        self,
        url: str,
        destination: Path,
        config: Optional[DownloadConfig] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        """
        Download a file from URL to destination with progress tracking.
        
        Args:
            url: File URL to download
            destination: Local path to save the file
            config: Download configuration
            progress_callback: Callback for progress updates (bytes_downloaded, total_bytes)
            
        Returns:
            Number of bytes downloaded
            
        Raises:
            DownloadError: If download fails
        """

        config = config or DownloadConfig()
        
        try:
            # Create parent directories if they don't exist
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Get file size for progress tracking
            head_response = self.client.head(url, timeout=config.timeout)
            total_size = int(head_response.headers.get('content-length', 0))
            
            # Set up progress tracking
            progress_bar = None
            if progress_callback or total_size > 0:
                progress_bar = tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=destination.name,
                    leave=False
                )
            
            def update_progress(chunk_bytes: int) -> None:
                """Update progress for each chunk."""
                if progress_bar:
                    progress_bar.update(chunk_bytes)
                if progress_callback:
                    progress_callback(chunk_bytes, total_size)
            
            # Download the file
            response: httpx.Response = self.retry_manager.execute(
                lambda: self.client.get(url, stream=True, timeout=config.timeout)
            )
            response.raise_for_status()
            
            bytes_downloaded = 0
            with open(destination, 'wb') as f:
                for chunk in response.iter_bytes(chunk_size=config.chunk_size):
                    if chunk:
                        f.write(chunk)
                        chunk_size = len(chunk)
                        bytes_downloaded += chunk_size
                        update_progress(chunk_size)
            
            if progress_bar:
                progress_bar.close()
            
            logger.debug(f"Downloaded {bytes_downloaded} bytes to {destination}")
            return bytes_downloaded
            
        except httpx.RequestError as e:
            # Clean up partially downloaded file
            if destination.exists():
                destination.unlink()
            raise DownloadError(f"Failed to download {url}: {e}")
        
        except Exception as e:
            # Clean up on any error
            if destination.exists():
                destination.unlink()
            raise DownloadError(f"Unexpected error during download: {e}")
    
    def download_file_with_progress(
        self,
        url: str,
        destination: Path,
        progress_info: ProgressInfo,
        filename: str,
        config: Optional[DownloadConfig] = None
    ) -> int:
        """
        Download a file with integrated progress tracking.
        
        Args:
            url: File URL to download
            destination: Local path to save the file
            progress_info: ProgressInfo object to update
            filename: Name of the file for progress display
            config: Download configuration
            
        Returns:
            Number of bytes downloaded
        """

        def progress_callback(
            chunk_bytes: int, 
            total_bytes: int
        ) -> None:
            progress_info.update_file_progress(chunk_bytes, filename)
        
        bytes_downloaded = self.download_file(
            url=url,
            destination=destination,
            config=config,
            progress_callback=progress_callback
        )
        
        progress_info.complete_file()
        return bytes_downloaded
    
    def save_content(
        self, 
        content: bytes, 
        destination: Path
    ) -> int:
        """
        Save content to a file.
        
        Args:
            content: Content to save as bytes
            destination: Local path to save the file
            
        Returns:
            Number of bytes written
        """

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            with open(destination, 'wb') as f:
                bytes_written = f.write(content)
            
            logger.debug(f"Saved {bytes_written} bytes to {destination}")
            return bytes_written
            
        except IOError as e:
            raise DownloadError(f"Failed to save file {destination}: {e}")
    
    def file_exists(self, path: Path) -> bool:
        """
        Check if a file exists and is accessible.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists and is accessible
        """

        return path.exists() and path.is_file()
    
    def directory_exists(self, path: Path) -> bool:
        """
        Check if a directory exists and is accessible.
        
        Args:
            path: Directory path to check
            
        Returns:
            True if directory exists and is accessible
        """

        return path.exists() and path.is_dir()
    
    def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure
            
        Raises:
            DownloadError: If directory cannot be created
        """

        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise DownloadError(f"Failed to create directory {path}: {e}")
    
    def get_file_size(self, path: Path) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            path: File path
            
        Returns:
            File size in bytes
            
        Raises:
            DownloadError: If file doesn't exist or is inaccessible
        """

        if not self.file_exists(path):
            raise DownloadError(f"File does not exist: {path}")
        
        try:
            return path.stat().st_size
        except OSError as e:
            raise DownloadError(
                f"Failed to get file size for {path}: {e}"
            )
        