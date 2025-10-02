from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .github import RepositoryInfo, GitReference

@dataclass
class CacheEntry:
    key: str
    repository: RepositoryInfo
    git_ref: GitReference
    content_hash: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
