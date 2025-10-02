from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List
from urllib.parse import urlparse

class RepositoryType(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"

@dataclass(frozen=True)
class GitReference:
    name: str
    ref_type: str  # 'branch', 'tag', 'commit'
    sha: Optional[str] = None

    def __post_init__(self) -> None:
        if self.ref_type not in ('branch', 'tag', 'commit'):
            raise ValueError(f"Invalid ref_type: {self.ref_type}")
        if self.ref_type == 'commit' and not self.sha:
            raise ValueError("SHA is required for commit references")

@dataclass(frozen=True)
class RepositoryInfo:
    owner: str
    name: str
    full_name: str
    url: str
    default_branch: str
    repo_type: RepositoryType
    size: int
    is_private: bool
    is_fork: bool
    created_at: datetime
    updated_at: datetime
    language: Optional[str] = None
    description: Optional[str] = None
    topics: List[str] = None

    @property
    def display_name(self):
        return f"{self.owner}/{self.name}"

    def __post_init__(self) -> None:
        if not self.owner or not self.name:
            raise ValueError("Repository owner and name are required")
        if not urlparse(self.url).netloc:
            raise ValueError(f"Invalid repository URL: {self.url}")

@dataclass
class GitHubFile:
    path: str
    type: str  # 'blob', 'tree', 'symlink'
    size: int
    download_url: Optional[str] = None
    sha: Optional[str] = None
    html_url: Optional[str] = None
