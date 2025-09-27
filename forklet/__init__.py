"""
Forklet - GitHub Repository Downloader.

A flexible, robust tool for downloading files and folders from GitHub repositories
with support for branches, tags, commits, and advanced filtering.
"""

from forklet.models.constants import VERSION 
from forklet.interfaces.api import GitHubDownloader
from forklet.models import (
    DownloadRequest, DownloadResult, DownloadStrategy, FilterCriteria,
    RepositoryInfo, GitReference, ProgressInfo, DownloadStatus
)

# Meta data
__version__ = VERSION
__author__ = "AllDotPy"
__description__ = "Download any file or folder from any GitHub repo by branch, tag, or commit with glob pattern filtering."

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
