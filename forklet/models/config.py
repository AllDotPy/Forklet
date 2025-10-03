"""
Configuration models for Forklet downloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class DownloadConfig:
    """
    Unified configuration for file downloads.
    
    Combines settings for both basic file downloads and API-level downloads.
    Provides comprehensive control over download behavior.
    """

    # Basic download settings
    chunk_size: int = 8192
    timeout: int = 300  # Increased to 300 to match API model default
    max_retries: int = 3
    show_progress: bool = False
    progress_callback: Optional[Callable[[int, int], None]] = None
    
    # Concurrency and performance settings
    max_concurrent_downloads: int = 5
    
    # File handling settings
    overwrite_existing: bool = False
    preserve_structure: bool = True


__all__ = [
    "DownloadConfig",
]


