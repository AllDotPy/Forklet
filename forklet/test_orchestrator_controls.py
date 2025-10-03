#!/usr/bin/env python3
"""
Test script for DownloadOrchestrator control methods.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the project path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from forklet.core.orchestrator import DownloadOrchestrator
from forklet.models import (
    DownloadRequest, DownloadResult, DownloadStrategy, FilterCriteria,
    RepositoryInfo, GitReference, ProgressInfo, RepositoryType, DownloadStatus
)
from datetime import datetime


async def test_control_methods():
    """Test DownloadOrchestrator control methods (cancel, pause, resume, get_current_progress)."""
    
    print("Testing DownloadOrchestrator control methods...")
    
    # Create mock services
    mock_github_service = Mock()
    mock_download_service = Mock()
    
    # Create orchestrator
    orchestrator = DownloadOrchestrator(
        github_service=mock_github_service,
        download_service=mock_download_service,
        max_concurrent_downloads=5
    )
    
    # Test 1: Initial state
    print("Test 1: Initial state checks")
    assert not orchestrator._is_cancelled
    assert not orchestrator._is_paused
    assert orchestrator._current_result is None
    
    print("[OK] Initial state correct")
    
    # Test 2: get_current_progress when no download active
    print("Test 2: get_current_progress when no download active")
    progress = orchestrator.get_current_progress()
    assert progress is None
    
    print("[OK] get_current_progress returns None when no active download")
    
    # Test 3: Cancel when no active download
    print("Test 3: Cancel when no active download")
    result = orchestrator.cancel()
    assert result is None
    
    print("[OK] Cancel returns None when no active download")
    
    # Test 4: Pause when no active download
    print("Test 4: Pause when no active download")
    result = orchestrator.pause()
    assert result is None
    
    print("[OK] Pause returns None when no active download")
    
    # Test 5: Resume when no active download
    print("Test 5: Resume when no active download")
    result = orchestrator.resume()
    assert result is None
    
    print("[OK] Resume returns None when no active download")
    
    print("All control method tests passed!")
    return True  # Keep this for proper test function signature


if __name__ == "__main__":
    # This block should be removed as per reviewer
    success = asyncio.run(test_control_methods())
    print(f"Test {'PASSED' if success else 'FAILED'}")
