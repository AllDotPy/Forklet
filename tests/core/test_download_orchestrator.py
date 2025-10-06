import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Make sure these import paths are correct for your project structure
from forklet.core.orchestrator import DownloadOrchestrator
from forklet.models import GitHubFile, DownloadStatus

# --- Test Fixtures for Setup ---

@pytest.fixture
def mock_services():
    """Creates mock objects for services used by the orchestrator."""
    github_service = MagicMock()
    download_service = MagicMock()
    github_service.get_repository_tree = AsyncMock()
    github_service.get_file_content = AsyncMock()
    download_service.save_content = AsyncMock(return_value=128)
    download_service.ensure_directory = AsyncMock()
    return github_service, download_service

@pytest.fixture
def orchestrator(mock_services):
    """Initializes the DownloadOrchestrator with mocked services."""
    github_service, download_service = mock_services
    orchestrator_instance = DownloadOrchestrator(
        github_service=github_service,
        download_service=download_service,
        max_concurrent_downloads=5
    )
    orchestrator_instance.reset_state()
    return orchestrator_instance

@pytest.fixture
def mock_request():
    """Creates a mock DownloadRequest object for use in tests."""
    request = MagicMock()
    request.repository.owner = "test-owner"
    request.repository.name = "test-repo"
    request.repository.display_name = "test-owner/test-repo"
    request.git_ref = "main"
    request.filters = MagicMock()
    request.filters.include_patterns = []
    request.filters.exclude_patterns = []
    request.destination = Path("/fake/destination")
    request.create_destination = True
    request.overwrite_existing = False
    request.preserve_structure = True
    request.show_progress_bars = False
    return request

# --- Test Cases ---

class TestDownloadOrchestrator:

    def test_initialization_sets_properties_correctly(self, orchestrator):
        """Verify that max_concurrent_downloads is correctly set."""
        assert orchestrator.max_concurrent_downloads == 5
        assert orchestrator._semaphore._value == 5
        assert not orchestrator._is_cancelled

    @pytest.mark.asyncio
    async def test_execute_download_success(self, orchestrator, mock_services, mock_request):
        """Simulate a successful download with mocked services."""
        github_service, _ = mock_services
        mock_file_list = [MagicMock(spec=GitHubFile, path="file1.txt", size=100)]
        github_service.get_repository_tree.return_value = mock_file_list

        with patch.object(orchestrator, '_download_files_concurrently', new_callable=AsyncMock) as mock_downloader, \
             patch('forklet.core.orchestrator.FilterEngine') as mock_filter_engine:
            
            mock_downloader.return_value = (["file1.txt"], {})
            mock_filter_engine.return_value.filter_files.return_value.included_files = mock_file_list

            result = await orchestrator.execute_download(request=mock_request)
            
            mock_downloader.assert_awaited_once()
            assert result.status == DownloadStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_download_repo_fetch_fails(self, orchestrator, mock_services, mock_request):
        """Test error handling when repository tree fetch fails."""
        github_service, _ = mock_services
        github_service.get_repository_tree.side_effect = Exception("API limit reached")
        
        result = await orchestrator.execute_download(request=mock_request)
        
        assert result.status == DownloadStatus.FAILED
        assert "API limit reached" in result.error_message

    def test_cancel_sets_flag_and_logs(self, orchestrator):
        """Test cancel() -> sets _is_cancelled=True and logs when a download is active."""
        orchestrator._current_result = MagicMock()

        with patch('forklet.core.orchestrator.logger') as mock_logger:
            orchestrator.cancel()
            assert orchestrator._is_cancelled is True
            mock_logger.info.assert_called_with("Download cancelled by user")

    @pytest.mark.asyncio
    async def test_pause_and_resume_flow(self, orchestrator, mock_services, mock_request):
        """Tests the full pause and resume flow in a stable, controlled manner."""
        github_service, _ = mock_services
        # --- THIS IS THE FIX ---
        # The mock file MUST have a 'size' attribute for the sum() calculation.
        mock_file_list = [MagicMock(spec=GitHubFile, path="file1.txt", size=100)]
        # -----------------------
        github_service.get_repository_tree.return_value = mock_file_list
        
        download_can_complete = asyncio.Event()

        async def wait_for_signal_to_finish(*args, **kwargs):
            await download_can_complete.wait()
            return (["file1.txt"], {})
        
        with patch.object(orchestrator, '_download_files_concurrently', side_effect=wait_for_signal_to_finish), \
             patch('forklet.core.orchestrator.FilterEngine') as mock_filter_engine:
            
            mock_filter_engine.return_value.filter_files.return_value.included_files = mock_file_list

            download_task = asyncio.create_task(orchestrator.execute_download(mock_request))
            
            await asyncio.sleep(0.01)

            if download_task.done() and download_task.exception():
                raise download_task.exception()
            
            assert orchestrator._current_result is not None, "Orchestrator._current_result was not set."
            
            await orchestrator.pause()
            assert orchestrator._is_paused is True
            assert orchestrator._current_result.status == DownloadStatus.PAUSED

            await orchestrator.resume()
            assert orchestrator._is_paused is False
            assert orchestrator._current_result.status == DownloadStatus.IN_PROGRESS

            download_can_complete.set()

            final_result = await download_task
            assert final_result.status == DownloadStatus.COMPLETED

    def test_get_current_progress_returns_none_when_inactive(self, orchestrator):
        """Test get_current_progress() -> returns None when no download is active."""
        assert orchestrator.get_current_progress() is None