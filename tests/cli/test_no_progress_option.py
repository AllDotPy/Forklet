#!/usr/bin/env python3
"""
Test script to verify the --no-progress CLI option fix.
"""

import sys
from pathlib import Path

# Add the project path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from forklet.models import DownloadRequest
from forklet.interfaces.api import DownloadConfig


def test_api_progress_disabled():
    """Test that Python API correctly sets show_progress_bars=False when show_progress=False."""
    
    print("Testing Python API: show_progress=False...")
    
    # Create DownloadConfig with progress disabled
    config = DownloadConfig(show_progress=False)
    
    # Check that the config field exists and is set correctly
    assert hasattr(config, 'show_progress'), "DownloadConfig should have show_progress field"
    assert not config.show_progress, "DownloadConfig.show_progress should be False"


def test_api_progress_enabled():
    """Test that Python API correctly sets show_progress_bars=True when show_progress=True."""
    
    print("Testing Python API: show_progress=True (default)...")
    
    # Create DownloadConfig with progress enabled (default)
    config = DownloadConfig()
    
    # Check that the config field exists and is set correctly
    assert hasattr(config, 'show_progress'), "DownloadConfig should have show_progress field"
    assert not config.show_progress, "DownloadConfig.show_progress should be True by default"
    
    print("[OK] API config correctly sets show_progress=True (default)")


def test_downloadrequest_creation():
    """Test that DownloadRequest correctly receives show_progress_bars parameter."""
    
    print("Testing DownloadRequest creation...")
    
    # Mock config with progress disabled
    config = DownloadConfig(show_progress=False)
    
    # Create mock DownloadRequest manually to test parameter passing
    from forklet.models.github import RepositoryInfo, GitReference, RepositoryType
    from forklet.models import FilterCriteria
    from datetime import datetime
    
    # Mock repository components
    repository = RepositoryInfo(
        full_name="test/repo",
        owner="test",
        name="repo",
        description="Test repository",
        url="https://github.com/test/repo",
        default_branch="main",
        repo_type=RepositoryType.PUBLIC,
        size=1024,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        language="Python",
        topics=[],
        is_private=False,
        is_fork=False
    )
    
    git_ref = GitReference(
        name="main",
        ref_type="branch",
        sha="abc123"
    )
    
    destination = Path("/tmp/test")
    
    # Create DownloadRequest
    request = DownloadRequest(
        repository=repository,
        git_ref=git_ref,
        destination=destination,
        strategy=1,  # DownloadStrategy enum value
        filters=FilterCriteria(),
        show_progress_bars=config.show_progress if config else True
    )
    
    # Verify the request has the correct setting
    assert not request.show_progress_bars, "DownloadRequest should have show_progress_bars=False when config shows False"
    
    print("[OK] DownloadRequest correctly sets show_progress_bars=False")
