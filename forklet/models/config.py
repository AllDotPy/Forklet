from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class DownloadConfig:
    chunk_size: int = 8192
    timeout: int = 30
    max_retries: int = 3
    show_progress: bool = False
    progress_callback: Optional[Callable[[int, int], None]] = None
