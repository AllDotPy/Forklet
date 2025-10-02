"""
Configuration models for Forklet downloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class DownloadConfig:
    """Configuration for file downloads."""

    chunk_size: int = 8192
    timeout: int = 30
    max_retries: int = 3
    show_progress: bool = False
    progress_callback: Optional[Callable[[int, int], None]] = None


__all__ = [
    "DownloadConfig",
]


