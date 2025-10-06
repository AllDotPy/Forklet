"""
GitHub domain models for Forklet.

This module contains strongly typed data classes and enums representing
GitHub-specific entities and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse


class RepositoryType(Enum):
    """Enumeration of supported repository types."""

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


@dataclass(frozen=True)
class GitReference:
    """Immutable representation of a Git reference (branch, tag, or commit)."""

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
    """Immutable repository metadata container."""

    owner: str
    name: str
    full_name: str
    url: str
    default_branch: str
    repo_type: RepositoryType
    size: int  # Size in KB
    is_private: bool
    is_fork: bool
    created_at: datetime
    updated_at: datetime
    language: Optional[str] = None
    description: Optional[str] = None
    topics: List[str] = field(default_factory=list)

    @property
    def display_name(self):
        return f'{self.owner}/{self.name}'

    def __post_init__(self) -> None:
        if not self.owner or not self.name:
            raise ValueError("Repository owner and name are required")

        parsed_url = urlparse(self.url)
        if not parsed_url.netloc:
            raise ValueError(f"Invalid repository URL: {self.url}")


@dataclass
class GitHubFile:
    """Represents a file in GitHub repository."""

    path: str
    type: str  # 'blob', 'tree', 'symlink'
    size: int
    download_url: Optional[str] = None
    sha: Optional[str] = None
    html_url: Optional[str] = None


__all__ = [
    "RepositoryType",
    "GitReference",
    "RepositoryInfo",
    "GitHubFile",
]


