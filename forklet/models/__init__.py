"""
Core data models API surface for Forklet.

This file re-exports model classes from domain-specific modules to preserve
backward compatibility for imports like `from forklet.models import X`.
"""

from .github import (
    RepositoryType,
    GitReference,
    RepositoryInfo,
    GitHubFile,
)
from .download import (
    DownloadStrategy,
    DownloadStatus,
    FilterCriteria,
    DownloadRequest,
    FileDownloadInfo,
    ProgressInfo,
    DownloadResult,
    CacheEntry,
)
from .config import DownloadConfig

__all__ = [
    # GitHub models
    "RepositoryType",
    "GitReference",
    "RepositoryInfo",
    "GitHubFile",
    # Download models
    "DownloadStrategy",
    "DownloadStatus",
    "FilterCriteria",
    "DownloadRequest",
    "FileDownloadInfo",
    "ProgressInfo",
    "DownloadResult",
    "CacheEntry",
    # Config models
    "DownloadConfig",
]
