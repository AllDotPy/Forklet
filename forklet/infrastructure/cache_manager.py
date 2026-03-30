"""
Cache manager for storing and retrieving cached data.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timedelta

from ..models import CacheEntry, RepositoryInfo, GitReference
from forklet.infrastructure.logger import logger


class CacheManager:
    """
    Manages caching of data to disk with expiration and access tracking.
    """

    def __init__(
        self, cache_dir: Optional[Path] = None, default_expire_hours: int = 24
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cache files. If None, uses a default directory.
            default_expire_hours: Default expiration time in hours for cache entries.
        """
        if cache_dir is None:
            # Use platform-appropriate cache directory
            cache_dir = Path.home() / ".cache" / "forklet"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_expire_hours = default_expire_hours
        logger.debug(f"Cache manager initialized with directory: {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            key: Cache key

        Returns:
            Path to the cache file
        """
        # Use a hash of the key to avoid filesystem issues with special characters
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Retrieve a cache entry by key.

        Args:
            key: Cache key

        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r") as f:
                data = json.load(f)

            # Reconstruct CacheEntry object
            entry = CacheEntry(
                key=data["key"],
                repository=RepositoryInfo(**data["repository"]),
                git_ref=GitReference(**data["git_ref"]),
                content_hash=data["content_hash"],
                created_at=datetime.fromisoformat(data["created_at"]),
                expires_at=datetime.fromisoformat(data["expires_at"])
                if data["expires_at"]
                else None,
                access_count=data["access_count"],
                last_accessed=datetime.fromisoformat(data["last_accessed"]),
            )

            # Check if expired
            if entry.is_expired:
                logger.debug(f"Cache entry expired for key: {key}")
                self.delete(key)
                return None

            # Update access info
            entry.touch()
            self._update_cache_file(entry)

            logger.debug(f"Cache hit for key: {key}")
            return entry

        except Exception as e:
            logger.warning(f"Failed to read cache entry for key {key}: {e}")
            # Delete corrupted cache file
            self.delete(key)
            return None

    def set(self, entry: CacheEntry) -> None:
        """
        Store a cache entry.

        Args:
            entry: CacheEntry to store
        """
        # Set expiration if not already set
        if entry.expires_at is None:
            entry.expires_at = datetime.now() + timedelta(
                hours=self.default_expire_hours
            )

        try:
            self._update_cache_file(entry)
            logger.debug(f"Cached entry for key: {entry.key}")
        except Exception as e:
            logger.error(f"Failed to write cache entry for key {entry.key}: {e}")

    def _update_cache_file(self, entry: CacheEntry) -> None:
        """
        Write a cache entry to disk.

        Args:
            entry: CacheEntry to write
        """
        cache_path = self._get_cache_path(entry.key)

        # Convert entry to dictionary for JSON serialization
        data = {
            "key": entry.key,
            "repository": {
                "owner": entry.repository.owner,
                "name": entry.repository.name,
                "full_name": entry.repository.full_name,
                "url": entry.repository.url,
                "default_branch": entry.repository.default_branch,
                "repo_type": entry.repository.repo_type.value,
                "size": entry.repository.size,
                "is_private": entry.repository.is_private,
                "is_fork": entry.repository.is_fork,
                "created_at": entry.repository.created_at.isoformat(),
                "updated_at": entry.repository.updated_at.isoformat(),
                "language": entry.repository.language,
                "description": entry.repository.description,
                "topics": entry.repository.topics,
            },
            "git_ref": {
                "name": entry.git_ref.name,
                "ref_type": entry.git_ref.ref_type,
                "sha": entry.git_ref.sha,
            },
            "content_hash": entry.content_hash,
            "created_at": entry.created_at.isoformat(),
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
            "access_count": entry.access_count,
            "last_accessed": entry.last_accessed.isoformat(),
        }

        # Write to a temporary file first, then rename for atomicity
        temp_path = cache_path.with_suffix(".json.tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(cache_path)

    def delete(self, key: str) -> bool:
        """
        Delete a cache entry.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Deleted cache entry for key: {key}")
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)

                expires_at = data.get("expires_at")
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        cache_file.unlink()
                        count += 1
            except Exception as e:
                # If we can't read the file, delete it to be safe
                logger.warning(f"Failed to read cache file {cache_file}, deleting: {e}")
                cache_file.unlink()
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")
        return count
