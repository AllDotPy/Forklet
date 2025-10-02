"""
Core data models for Forklet (GitHub Repository Downloader).
"""

from .github import RepositoryType, GitReference, RepositoryInfo, GitHubFile
from .download import (
    DownloadStrategy, DownloadStatus, 
    FilterCriteria, DownloadRequest, FileDownloadInfo, 
    ProgressInfo, DownloadResult
)
from .config import DownloadConfig
from .cache import CacheEntry

__all__ = [
    "RepositoryType", "GitReference", "RepositoryInfo", "GitHubFile",
    "DownloadStrategy", "DownloadStatus", "FilterCriteria", "DownloadRequest",
    "FileDownloadInfo", "ProgressInfo", "DownloadResult",
    "DownloadConfig", "CacheEntry"
]
