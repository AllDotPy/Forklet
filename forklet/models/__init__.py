"""
Core data models for Forklet (GitHub Repository Downloader).

This module contains strongly typed data classes that represent the core 
business entities used throughout the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse


####
##      REPO TYPE ENUM
#####
class RepositoryType(Enum):
    """Enumeration of supported repository types."""
    
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


####
##      DOWNLOAD STRATEGY ENUM
#####
class DownloadStrategy(Enum):
    """Available download strategies for repository content."""
    
    ARCHIVE = "archive"             # Download as ZIP/TAR archive
    INDIVIDUAL = "individual"       # Download files individually via API
    GIT_CLONE = "git_clone"         # Use git clone (for complete history)
    SPARSE_CHECKOUT = "sparse"      # Git sparse-checkout for partial downloads


####
##      DOWNLOAD STATUS ENUM
#####
class DownloadStatus(Enum):
    """Status enumeration for download operations."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


####
##      GIT REFERENCE MODEL CLASS
#####
@dataclass(frozen=True)
class GitReference:
    """Immutable representation of a Git reference (branch, tag, or commit)."""
    
    name: str
    ref_type: str  # 'branch', 'tag', 'commit'
    sha: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate the Git reference after initialization."""

        if self.ref_type not in ('branch', 'tag', 'commit'):
            raise ValueError(
                f"Invalid ref_type: {self.ref_type}"
            )
        
        if self.ref_type == 'commit' and not self.sha:
            raise ValueError(
                "SHA is required for commit references"
            )


####
##      REPO INFORMATIONS MODEL
#####
@dataclass(frozen=True)
class RepositoryInfo:
    """Immutable repository metadata container."""
    
    owner: str
    name: str
    full_name: str
    url: str
    default_branch: str
    repo_type: RepositoryType
    size: int  # Size in KB
    is_private: bool
    is_fork: bool
    created_at: datetime
    updated_at: datetime
    language: Optional[str] = None
    description: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate repository information after initialization."""

        if not self.owner or not self.name:
            raise ValueError(
                "Repository owner and name are required"
            )
        
        parsed_url = urlparse(self.url)
        if not parsed_url.netloc:
            raise ValueError(
                f"Invalid repository URL: {self.url}"
            )


####
##      REPO CONTENT FLITERING CRITERIA
#####
@dataclass
class FilterCriteria:
    """Flexible filtering criteria for repository content."""
    
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    max_file_size: Optional[int] = None  # Size in bytes
    min_file_size: Optional[int] = None  # Size in bytes
    file_extensions: Set[str] = field(default_factory=set)
    excluded_extensions: Set[str] = field(default_factory=set)
    include_hidden: bool = False
    include_binary: bool = True
    target_paths: List[str] = field(default_factory=list)  # Specific paths to download
    
    def matches_path(self, path: str) -> bool:
        """
        Check if a given path matches the filter criteria.
        
        Args:
            path: The file path to check
            
        Returns:
            True if the path matches the criteria, False otherwise
        """
        import fnmatch
        
        # Check target paths first (if specified)
        if self.target_paths:
            if not any(
                path.startswith(target) 
                for target in self.target_paths
            ):
                return False
        
        # Check include patterns
        if self.include_patterns:
            if not any(
                fnmatch.fnmatch(path, pattern) 
                for pattern in self.include_patterns
            ):
                return False
        
        # Check exclude patterns
        if self.exclude_patterns:
            if any(
                fnmatch.fnmatch(path, pattern) 
                for pattern in self.exclude_patterns
            ):
                return False
        
        # Check hidden files
        if (
            not self.include_hidden 
            and any(part.startswith('.') 
            for part in Path(path).parts)
        ):
            return False
        
        # Check file extensions
        file_ext = Path(path).suffix.lower()
        if self.file_extensions and file_ext not in self.file_extensions:
            return False
        
        if file_ext in self.excluded_extensions:
            return False
        
        return True


####
##      DOWNLOAD REQUEST MODEL
#####
@dataclass
class DownloadRequest:
    """Comprehensive download request specification."""
    
    repository: RepositoryInfo
    git_ref: GitReference
    destination: Path
    strategy: DownloadStrategy
    filters: FilterCriteria = field(default_factory=FilterCriteria)
    
    # Download options
    overwrite_existing: bool = False
    create_destination: bool = True
    preserve_structure: bool = True
    extract_archives: bool = True
    
    # Performance options
    max_concurrent_downloads: int = 5
    chunk_size: int = 8192              # Download chunk size in bytes
    timeout: int = 300                  # Timeout in seconds
    
    # Authentication
    token: Optional[str] = None
    
    # Metadata
    request_id: str = field(
        default_factory = lambda: f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate download request after initialization."""

        if not self.destination:
            raise ValueError("Destination path is required")
        
        if self.max_concurrent_downloads <= 0:
            raise ValueError("max_concurrent_downloads must be positive")
        
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")


####
##      FFILE DOWNLOAD MODEL
#####
@dataclass
class FileDownloadInfo:
    """Information about a single file to be downloaded."""
    
    path: str
    url: str
    size: int
    sha: str
    download_url: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate file download information."""

        if not self.path or not self.url:
            raise ValueError("File path and URL are required")
        
        if self.size < 0:
            raise ValueError("File size cannot be negative")


####
##      PROOGRESSION MODEL
#####
@dataclass
class ProgressInfo:
    """Real-time progress tracking information."""
    
    total_files: int
    downloaded_files: int
    total_bytes: int
    downloaded_bytes: int
    current_file: Optional[str] = None
    download_speed: float = 0.0         # Bytes per second
    eta_seconds: Optional[float] = None
    started_at: datetime = field(default_factory=datetime.now)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate download progress as percentage."""

        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100.0
    
    @property
    def files_percentage(self) -> float:
        """Calculate file count progress as percentage."""

        if self.total_files == 0:
            return 0.0
        return (self.downloaded_files / self.total_files) * 100.0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""

        return (datetime.now() - self.started_at).total_seconds()

    def update_file_progress(
        self, 
        bytes_downloaded: int, 
        current_file: Optional[str] = None
    ) -> None:
        """Update progress for the current file."""

        self.downloaded_bytes += bytes_downloaded
        if current_file:
            self.current_file = current_file
    
    def complete_file(self) -> None:
        """Mark a file as completed."""
        
        self.downloaded_files += 1
        self.current_file = None


####
##      DOWNLOAD RESULT MODEL
#####
@dataclass
class DownloadResult:
    """Comprehensive result of a download operation."""
    
    request: DownloadRequest
    status: DownloadStatus
    progress: ProgressInfo
    
    # Results
    downloaded_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: Dict[str, str] = field(default_factory=dict)  # filename -> error message
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Statistics
    total_download_time: Optional[float] = None
    average_speed: Optional[float] = None
    cache_hits: int = 0
    api_calls_made: int = 0
    
    @property
    def is_successful(self) -> bool:
        """Check if the download was successful."""

        return (
            self.status == DownloadStatus.COMPLETED 
            and not self.failed_files
        )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""

        total = len(self.downloaded_files) + len(self.failed_files)
        if total == 0:
            return 0.0
        return (len(self.downloaded_files) / total) * 100.0
    
    def mark_completed(self) -> None:
        """Mark the download as completed and calculate final statistics."""

        self.completed_at = datetime.now()
        self.status = (
            DownloadStatus.COMPLETED 
            if not self.failed_files 
            else DownloadStatus.FAILED
        )
        
        if self.completed_at:
            self.total_download_time = (self.completed_at - self.started_at).total_seconds()
            if (
                self.total_download_time > 0 
                and self.progress.downloaded_bytes > 0
            ):
                self.average_speed = self.progress.downloaded_bytes / self.total_download_time


####
##      CACHE ENTRY MODEL
#####
@dataclass
class CacheEntry:
    """Cache entry for downloaded repository metadata and content."""
    
    key: str
    repository: RepositoryInfo
    git_ref: GitReference
    content_hash: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""

        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """Update last accessed time and increment access count."""

        self.last_accessed = datetime.now()
        self.access_count += 1


####
##      GITHUB FILE MODEL
#####
@dataclass
class GitHubFile:
    """Represents a file in GitHub repository."""
    
    path: str
    type: str  # 'file', 'dir', 'symlink'
    size: int
    download_url: Optional[str] = None
    sha: Optional[str] = None
    html_url: Optional[str] = None
