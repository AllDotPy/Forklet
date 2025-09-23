"""
Configuration settings for Forklet GitHub Repository Downloader.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


####
##      FORKLET STTINGS MODEL CLASS
#####
@dataclass
class AppSettings:
    """Application settings and configuration."""
    
    # GitHub API settings
    github_api_url: str = "https://api.github.com"
    github_token: Optional[str] = field(
        default_factory=lambda: os.getenv('GITHUB_TOKEN')
    )
    default_timeout: int = 30
    max_retries: int = 3
    
    # Download settings
    default_concurrent_downloads: int = 5
    default_chunk_size: int = 8192
    default_download_timeout: int = 300
    max_file_size: Optional[int] = 100 * 1024 * 1024  # 100MB
    
    # Cache settings
    cache_enabled: bool = True
    cache_directory: Path = field(
        default_factory=lambda: Path.home() / ".forklet" / "cache"
    )
    cache_ttl_hours: int = 24
    max_cache_size_mb: int = 1024  # 1GB
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[Path] = field(
        default_factory=lambda: Path.home() / ".forklet" / "logs" / "app.log"
    )
    
    # UI settings
    progress_bar_enabled: bool = True
    progress_update_interval: float = 0.1  # seconds
    
    def __post_init__(self) -> None:
        """Validate settings and ensure directories exist."""

        # Ensure cache directory exists
        if self.cache_enabled:
            self.cache_directory.mkdir(parents=True, exist_ok=True)
        
        # Ensure log directory exists
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'AppSettings':
        """
        Create settings from environment variables.
        
        Returns:
            AppSettings configured from environment
        """
        return cls(
            github_token = os.getenv('GITHUB_TOKEN'),
            default_concurrent_downloads = int(os.getenv('FORKLET_CONCURRENT_DOWNLOADS', '5')),
            cache_enabled = os.getenv('FORKLET_CACHE_ENABLED', 'true').lower() == 'true',
            log_level = os.getenv('FORKLET_LOG_LEVEL', 'INFO')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""

        return {
            'github_api_url': self.github_api_url,
            'github_token': '***' if self.github_token else None,
            'default_timeout': self.default_timeout,
            'max_retries': self.max_retries,
            'default_concurrent_downloads': self.default_concurrent_downloads,
            'default_chunk_size': self.default_chunk_size,
            'default_download_timeout': self.default_download_timeout,
            'max_file_size': self.max_file_size,
            'cache_enabled': self.cache_enabled,
            'cache_directory': str(self.cache_directory),
            'cache_ttl_hours': self.cache_ttl_hours,
            'max_cache_size_mb': self.max_cache_size_mb,
            'log_level': self.log_level,
            'log_file': str(self.log_file) if self.log_file else None,
            'progress_bar_enabled': self.progress_bar_enabled,
            'progress_update_interval': self.progress_update_interval
        }


# Global settings instance
settings = AppSettings()
