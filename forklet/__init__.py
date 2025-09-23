"""
Forklet - GitHub Repository Downloader.

A flexible, robust tool for downloading files and folders from GitHub repositories
with support for branches, tags, commits, and advanced filtering.
"""

__version__ = "0.1.0"
__author__ = "AllDotPy"
__description__ = "Download any file or folder from any GitHub repo by branch, tag, or commit with glob pattern filtering."

# from forklet.interfaces.api import GitHubDownloader
from forklet.models import (
    DownloadRequest, DownloadResult, DownloadStrategy, FilterCriteria,
    RepositoryInfo, GitReference, ProgressInfo, DownloadStatus
)

# Public API
__all__ = [
    'GitHubDownloader',
    'DownloadRequest',
    'DownloadResult',
    'DownloadStrategy',
    'FilterCriteria',
    'RepositoryInfo',
    'GitReference',
    'ProgressInfo',
    'DownloadStatus'
]
