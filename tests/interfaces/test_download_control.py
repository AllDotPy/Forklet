"""
Unit tests for download control functionality in GitHubDownloader API.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from forklet.interfaces.api import GitHubDownloader
from forklet.models import DownloadResult, DownloadStatus, ProgressInfo


class TestDownloadControl:
    """Test cases for download control functionality."""
    
    def test_cancel_current_download_success(self):
        """Test successful cancellation of current download."""
        # Create downloader
        downloader = GitHubDownloader()
        
        # Mock the orchestrator's cancel method
        mock_result = Mock(spec=DownloadResult)
        mock_result.status = DownloadStatus.CANCELLED
        downloader.orchestrator.cancel = Mock(return_value=mock_result)
        
        # Call cancel
        result = downloader.cancel_current_download()
        
        # Verify
        assert result == mock_result
        assert result.status == DownloadStatus.CANCELLED
        downloader.orchestrator.cancel.assert_called_once()
    
    def test_cancel_current_download_no_active(self):
        """Test cancellation when no download is active."""
        downloader = GitHubDownloader()
        downloader.orchestrator.cancel = Mock(return_value=None)
        
        result = downloader.cancel_current_download()
        
        assert result is None
        downloader.orchestrator.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pause_current_download_success(self):
        """Test successful pausing of current download."""
        downloader = GitHubDownloader()
        
        # Mock the orchestrator's pause method
        mock_result = Mock(spec=DownloadResult)
        mock_result.status = DownloadStatus.PAUSED
        downloader.orchestrator.pause = AsyncMock(return_value=mock_result)
        
        # Call pause
        result = await downloader.pause_current_download()
        
        # Verify
        assert result == mock_result
        assert result.status == DownloadStatus.PAUSED
        downloader.orchestrator.pause.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pause_current_download_no_active(self):
        """Test pausing when no download is active."""
        downloader = GitHubDownloader()
        downloader.orchestrator.pause = AsyncMock(return_value=None)
        
        result = await downloader.pause_current_download()
        
        assert result is None
        downloader.orchestrator.pause.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_current_download_success(self):
        """Test successful resuming of paused download."""
        downloader = GitHubDownloader()
        
        # Mock the orchestrator's resume method
        mock_result = Mock(spec=DownloadResult)
        mock_result.status = DownloadStatus.IN_PROGRESS
        downloader.orchestrator.resume = AsyncMock(return_value=mock_result)
        
        # Call resume
        result = await downloader.resume_current_download()
        
        # Verify
        assert result == mock_result
        assert result.status == DownloadStatus.IN_PROGRESS
        downloader.orchestrator.resume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_current_download_no_paused(self):
        """Test resuming when no download is paused."""
        downloader = GitHubDownloader()
        downloader.orchestrator.resume = AsyncMock(return_value=None)
        
        result = await downloader.resume_current_download()
        
        assert result is None
        downloader.orchestrator.resume.assert_called_once()
    
    def test_get_download_progress_with_active_download(self):
        """Test getting progress when download is active."""
        downloader = GitHubDownloader()
        
        # Mock progress info
        mock_progress = Mock(spec=ProgressInfo)
        mock_progress.total_files = 100
        mock_progress.downloaded_files = 50
        mock_progress.progress_percentage = 50.0
        
        downloader.orchestrator.get_current_progress = Mock(return_value=mock_progress)
        
        # Call get_progress
        result = downloader.get_download_progress()
        
        # Verify
        assert result == mock_progress
        assert result.progress_percentage == 50.0
        downloader.orchestrator.get_current_progress.assert_called_once()
    
    def test_get_download_progress_no_active_download(self):
        """Test getting progress when no download is active."""
        downloader = GitHubDownloader()
        downloader.orchestrator.get_current_progress = Mock(return_value=None)
        
        result = downloader.get_download_progress()
        
        assert result is None
        downloader.orchestrator.get_current_progress.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_control_workflow(self):
        """Test complete workflow: start -> pause -> resume -> cancel."""
        downloader = GitHubDownloader()
        
        # Mock orchestrator methods
        paused_result = Mock(spec=DownloadResult)
        paused_result.status = DownloadStatus.PAUSED
        
        resumed_result = Mock(spec=DownloadResult)
        resumed_result.status = DownloadStatus.IN_PROGRESS
        
        cancelled_result = Mock(spec=DownloadResult)
        cancelled_result.status = DownloadStatus.CANCELLED
        
        downloader.orchestrator.pause = AsyncMock(return_value=paused_result)
        downloader.orchestrator.resume = AsyncMock(return_value=resumed_result)
        downloader.orchestrator.cancel = Mock(return_value=cancelled_result)
        
        # Test workflow
        # 1. Pause
        result = await downloader.pause_current_download()
        assert result.status == DownloadStatus.PAUSED
        
        # 2. Resume
        result = await downloader.resume_current_download()
        assert result.status == DownloadStatus.IN_PROGRESS
        
        # 3. Cancel
        result = downloader.cancel_current_download()
        assert result.status == DownloadStatus.CANCELLED
        
        # Verify all methods were called
        downloader.orchestrator.pause.assert_called_once()
        downloader.orchestrator.resume.assert_called_once()
        downloader.orchestrator.cancel.assert_called_once()


