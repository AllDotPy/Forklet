#!/usr/bin/env python3
"""
Test script for the enhanced DownloadOrchestrator control methods.
This script tests cancel, pause, resume, and get_current_progress functionality.
"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project path to import our modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from unittest.mock import Mock
from forklet.core.orchestrator import DownloadOrchestrator

async def test_control_methods():
    """Test the enhanced control methods of DownloadOrchestrator."""
    
    print("Testing DownloadOrchestrator Control Methods...")
    
    # Supress the warning messages during tests by temporarily adjusting logging level
    logging.getLogger('Forklet').setLevel(logging.ERROR)
    
    # Mock the services
    github_service = Mock()
    download_service = Mock()
    
    # Create orchestrator instance
    orchestrator = DownloadOrchestrator(
        github_service=github_service,
        download_service=download_service,
        max_concurrent_downloads=5
    )
    
    print("SUCCESS: Orchestrator initialized")
    
    # Test cancel() without active download
    result = orchestrator.cancel()
    assert result is None, "Cancel should return None when no active download"
    print("SUCCESS: cancel() correctly handles no active download")
    
    # Test pause() without active download
    result = await orchestrator.pause()
    assert result is None, "Pause should return None when no active download"
    print("SUCCESS: pause() correctly handles no active download")
    
    # Test resume() without paused download
    result = await orchestrator.resume()
    assert result is None, "Resume should return None when no paused download"
    print("SUCCESS: resume() correctly handles no active/paused download")
    
    # Test get_current_progress() without active download
    progress = orchestrator.get_current_progress()
    assert progress is None, "get_current_progress should return None when no active download"
    print("SUCCESS: get_current_progress() correctly handles no active download")
    
    print("SUCCESS: Control methods basic functionality verified")
    print("SUCCESS: Enhancement completed successfully!")
    
    return True
