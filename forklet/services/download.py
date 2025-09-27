"""
Service for downloading files with progress tracking and error handling.
"""

from typing import Optional, List
from pathlib import Path
import asyncio
import aiofiles

from tqdm.asyncio import tqdm as async_tqdm

from ..infrastructure.retry_manager import RetryManager
from ..infrastructure.error_handler import (
    handle_api_error, retry_on_error, DownloadError
)
from ..models import ProgressInfo, DownloadConfig

from forklet.infrastructure.logger import logger


####
##      DOWNLOAD SERVICE
#####
class DownloadService:
    """
    Async service for file operations: saving, creating directories, etc.
    Focused solely on file system operations - no network requests.
    """
    
    def __init__(self, retry_manager: Optional[RetryManager] = None):
        self.retry_manager = retry_manager or RetryManager()
    
    @retry_on_error(max_retries=3)
    @handle_api_error
    async def save_content(
        self,
        content: bytes,
        destination: Path,
        show_progress: bool = False,
        config: Optional[DownloadConfig] = None
    ) -> int:
        """
        Save content to a file asynchronously.
        
        Args:
            content: Content to save as bytes
            destination: Local path to save the file
            show_progress: Whether to show progress bar
            config: Download configuration
            
        Returns:
            Number of bytes written
            
        Raises:
            DownloadError: If save operation fails
        """

        config = config or DownloadConfig()
        
        try:
            # Create parent directories if they don't exist
            await self.ensure_directory(destination.parent)
            
            # Setup progress tracking
            total_size = len(content)
            progress_bar = None
            
            if show_progress and total_size > 1024:  # Only show for files > 1KB
                progress_bar = async_tqdm(
                    total = total_size,
                    unit = 'B',
                    unit_scale = True,
                    desc = destination.name,
                    leave = False
                )
            
            bytes_written = 0
            
            # Write file in chunks to allow for progress tracking
            async with aiofiles.open(destination, 'wb') as f:
                for i in range(0, total_size, config.chunk_size):
                    chunk = content[i:i + config.chunk_size]
                    await f.write(chunk)
                    chunk_size = len(chunk)
                    bytes_written += chunk_size
                    
                    if progress_bar:
                        progress_bar.update(chunk_size)
                    
                    # Allow other tasks to run
                    if i % (config.chunk_size * 10) == 0:
                        await asyncio.sleep(0)
            
            if progress_bar:
                progress_bar.close()
            
            logger.debug(f"Saved {bytes_written} bytes to {destination}")
            return bytes_written
            
        except IOError as e:
            raise DownloadError(
                f"Failed to save file {destination}: {e}"
            )
        except Exception as e:
            raise DownloadError(
                f"Unexpected error saving file {destination}: {e}"
            )
    
    async def save_content_with_progress(
        self,
        content: bytes,
        destination: Path,
        progress_info: ProgressInfo,
        filename: str,
        config: Optional[DownloadConfig] = None
    ) -> int:
        """
        Save content with integrated progress tracking.
        
        Args:
            content: Content to save as bytes
            destination: Local path to save the file
            progress_info: ProgressInfo object to update
            filename: Name of the file for progress display
            config: Download configuration
            
        Returns:
            Number of bytes written
        """

        def progress_callback(
            chunk_bytes: int, 
            total_bytes: int
        ) -> None:
            progress_info.update_file_progress(
                chunk_bytes, filename
            )
        
        config = config or DownloadConfig(
            progress_callback = progress_callback
        )
        
        bytes_written = await self.save_content(
            content = content,
            destination = destination,
            config = config
        )
        
        progress_info.complete_file()
        return bytes_written
    
    async def file_exists(self, path: Path) -> bool:
        """
        Check if a file exists and is accessible asynchronously.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists and is accessible
        """

        try:
            return await asyncio.to_thread(
                lambda: path.exists() and path.is_file()
            )
        except Exception:
            return False
    
    async def directory_exists(self, path: Path) -> bool:
        """
        Check if a directory exists and is accessible asynchronously.
        
        Args:
            path: Directory path to check
            
        Returns:
            True if directory exists and is accessible
        """

        try:
            return await asyncio.to_thread(
                lambda: path.exists() and path.is_dir()
            )
        except Exception:
            return False
    
    async def ensure_directory(self, path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure
            
        Raises:
            DownloadError: If directory cannot be created
        """

        try:
            await asyncio.to_thread(
                lambda: path.mkdir(parents=True, exist_ok=True)
            )
        except OSError as e:
            raise DownloadError(
                f"Failed to create directory {path}: {e}"
            )
    
    async def get_file_size(self, path: Path) -> int:
        """
        Get the size of a file in bytes asynchronously.
        
        Args:
            path: File path
            
        Returns:
            File size in bytes
            
        Raises:
            DownloadError: If file doesn't exist or is inaccessible
        """
        
        if not await self.file_exists(path):
            raise DownloadError(f"File does not exist: {path}")
        
        try:
            return await asyncio.to_thread(
                lambda: path.stat().st_size
            )
        except OSError as e:
            raise DownloadError(
                f"Failed to get file size for {path}: {e}"
            )
    
    async def delete_file(self, path: Path) -> bool:
        """
        Delete a file asynchronously.
        
        Args:
            path: File path to delete
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            DownloadError: If deletion fails
        """

        if not await self.file_exists(path):
            return False
        
        try:
            await asyncio.to_thread(lambda: path.unlink())
            return True
        except OSError as e:
            raise DownloadError(
                f"Failed to delete file {path}: {e}"
            )
    
    async def create_backup(self, path: Path) -> Path:
        """
        Create a backup of an existing file.
        
        Args:
            path: Original file path
            
        Returns:
            Path to backup file
            
        Raises:
            DownloadError: If backup creation fails
        """

        if not await self.file_exists(path):
            raise DownloadError(
                f"Cannot backup non-existent file: {path}"
            )
        
        backup_path = path.with_suffix(f"{path.suffix}.backup")
        counter = 1
        
        # Find an available backup name
        while await self.file_exists(backup_path):
            backup_path = path.with_suffix(f"{path.suffix}.backup.{counter}")
            counter += 1
        
        try:
            # Read original file
            async with aiofiles.open(path, 'rb') as src:
                content = await src.read()
            
            # Write backup
            await self.save_content(content, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            raise DownloadError(f"Failed to create backup of {path}: {e}")
    
    async def batch_save_contents(
        self,
        contents_and_paths: List[tuple[bytes, Path]],
        show_progress: bool = False,
        max_concurrent: int = 10
    ) -> List[int]:
        """
        Save multiple contents to files concurrently.
        
        Args:
            contents_and_paths: List of (content, destination_path) tuples
            show_progress: Whether to show overall progress
            max_concurrent: Maximum concurrent save operations
            
        Returns:
            List of bytes written for each file
            
        Raises:
            DownloadError: If any save operation fails
        """

        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def save_with_semaphore(
            content: bytes, 
            path: Path
        ) -> int:
            async with semaphore:
                return await self.save_content(
                    content, path, show_progress = False
                )
        
        # Create tasks for all save operations
        tasks = [
            save_with_semaphore(content, path)
            for content, path in contents_and_paths
        ]
        
        # Execute with optional progress tracking
        if show_progress:
            results = []
            progress_bar = async_tqdm(
                total = len(tasks),
                desc = "Saving files",
                unit = "file"
            )
            
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                progress_bar.update(1)
            
            progress_bar.close()
            return results
        else:
            return await asyncio.gather(*tasks)
    
    async def cleanup_temp_files(
        self, 
        directory: Path, 
        pattern: str = "*.tmp"
    ) -> int:
        """
        Clean up temporary files in a directory.
        
        Args:
            directory: Directory to clean
            pattern: File pattern to match (default: *.tmp)
            
        Returns:
            Number of files cleaned up
        """

        if not await self.directory_exists(directory):
            return 0
        
        try:
            temp_files = await asyncio.to_thread(
                lambda: list(directory.glob(pattern))
            )
            
            cleanup_tasks = [
                self.delete_file(temp_file) 
                for temp_file in temp_files
            ]
            
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # Count successful deletions
            cleaned_count = sum(
                1 for result in results 
                if isinstance(result, bool) and result
            )
            
            logger.info(
                f"Cleaned up {cleaned_count} temporary files from {directory}"
            )
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup of {directory}: {e}")
            return 0
