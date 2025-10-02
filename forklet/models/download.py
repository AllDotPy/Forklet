from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set

from .github import RepositoryInfo, GitReference

class DownloadStrategy(Enum):
    ARCHIVE = "archive"
    INDIVIDUAL = "individual"
    GIT_CLONE = "git_clone"
    SPARSE_CHECKOUT = "sparse"

class DownloadStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class FilterCriteria:
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    max_file_size: Optional[int] = None
    min_file_size: Optional[int] = None
    file_extensions: Set[str] = field(default_factory=set)
    excluded_extensions: Set[str] = field(default_factory=set)
    include_hidden: bool = False
    include_binary: bool = True
    target_paths: List[str] = field(default_factory=list)

    def matches_path(self, path: str) -> bool:
        import fnmatch
        from pathlib import Path
        if self.target_paths and not any(path.startswith(t) for t in self.target_paths):
            return False
        if self.include_patterns and not any(fnmatch.fnmatch(path, p) for p in self.include_patterns):
            return False
        if self.exclude_patterns and any(fnmatch.fnmatch(path, p) for p in self.exclude_patterns):
            return False
        if not self.include_hidden and any(part.startswith('.') for part in Path(path).parts):
            return False
        ext = Path(path).suffix.lower()
        if self.file_extensions and ext not in self.file_extensions:
            return False
        if ext in self.excluded_extensions:
            return False
        return True

@dataclass
class DownloadRequest:
    repository: RepositoryInfo
    git_ref: GitReference
    destination: Path
    strategy: DownloadStrategy
    filters: FilterCriteria = field(default_factory=FilterCriteria)
    overwrite_existing: bool = False
    create_destination: bool = True
    preserve_structure: bool = True
    extract_archives: bool = True
    show_progress_bars: bool = True
    max_concurrent_downloads: int = 5
    chunk_size: int = 8192
    timeout: int = 300
    token: Optional[str] = None
    request_id: str = field(default_factory=lambda: f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class FileDownloadInfo:
    path: str
    url: str
    size: int
    sha: str
    download_url: Optional[str] = None

@dataclass
class ProgressInfo:
    total_files: int
    downloaded_files: int
    total_bytes: int
    downloaded_bytes: int
    current_file: Optional[str] = None
    download_speed: float = 0.0
    eta_seconds: Optional[float] = None
    started_at: datetime = field(default_factory=datetime.now)

@dataclass
class DownloadResult:
    request: DownloadRequest
    status: DownloadStatus
    progress: ProgressInfo
    downloaded_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: Dict[str, str] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
