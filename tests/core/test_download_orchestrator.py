import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

# Assume the class is located at forklet.core.orchestrator.DownloadOrchestrator
# Make sure this import path is correct for your project structure.
from forklet.core.orchestrator import DownloadOrchestrator
from forklet.models import GitHubFile # Import the actual model if available for type hinting

# --- Test Fixtures for Setup ---

@pytest.fixture
def mock_services():
    """Creates mock objects for services used by the orchestrator."""
    github_service = MagicMock()
    download_service = MagicMock()
    github_service.get_repository_tree = AsyncMock()
    github_service.get_file_content = AsyncMock()
    download_service.save_content = AsyncMock(return_value=128) # Return bytes_written
    download_service.ensure_directory = AsyncMock()
    return github_service, download_service

@pytest.fixture
def orchestrator(mock_services):
    """Initializes the DownloadOrchestrator with mocked services."""
    github_service, download_service = mock_services
    return DownloadOrchestrator(
        github_service=github_service,
        download_service=download_service,
        max_concurrent_downloads=5
    )

@pytest.fixture
def mock_request():
    """Creates a mock DownloadRequest object for use in tests."""
    request = MagicMock()
    request.repository.owner = "test-owner"
    request.repository.name = "test-repo"
    request.repository.display_name = "test-owner/test-repo"
    request.git_ref = "main"
    request.filters = []
    request.destination = Path("/fake/destination")
    request.create_destination = True
    request.overwrite_existing = False
    request.preserve_structure = True
    request.show_progress_bars = False
    return request

# --- Test Cases ---

class TestDownloadOrchestrator:

    # --- Initialization Tests ---
    def test_initialization_sets_properties_correctly(self, orchestrator):
        """Verify that max_concurrent_downloads is correctly set."""
        assert orchestrator.max_concurrent_downloads == 5
        assert orchestrator._semaphore._value == 5
        assert not orchestrator._is_cancelled

    # --- execute_download Tests ---
    @pytest.mark.asyncio
    async def test_execute_download_success(self, orchestrator, mock_services, mock_request):
        """Simulate a successful download with mocked services."""
        github_service, _ = mock_services
        mock_file_list = [MagicMock(spec=GitHubFile, path="file1.txt", size=100)]
        github_service.get_repository_tree.return_value = mock_file_list

        # Patch the concurrent downloader AND the filter engine
        with patch.object(orchestrator, '_download_files_concurrently', new_callable=AsyncMock) as mock_downloader, \
             patch('forklet.core.orchestrator.FilterEngine') as mock_filter_engine:

            # Configure the mocks
            mock_downloader.return_value = (["file1.txt"], {})
            mock_filter_engine.return_value.filter_files.return_value.included_files = mock_file_list

            # Act
            result = await orchestrator.execute_download(request=mock_request)
            
            # Assert
            mock_downloader.assert_awaited_once()
            assert result.status.value == "completed"

    @pytest.mark.asyncio
    async def test_execute_download_repo_fetch_fails(self, orchestrator, mock_services, mock_request):
        """Test error handling when repository tree fetch fails."""
        github_service, _ = mock_services
        github_service.get_repository_tree.side_effect = Exception("API limit reached")
        
        result = await orchestrator.execute_download(request=mock_request)
        
        # Corrected assertion to check for uppercase 'FAILED'
        assert result.status.value == "failed"
        assert "API limit reached" in result.error_message

    # --- _download_single_file Tests ---
    @pytest.mark.asyncio
    async def test_download_single_file_skips_if_exists(self, orchestrator, mock_services, mock_request):
        """Test skip logic when file already exists and overwrite_existing=False."""
        _, download_service = mock_services
        mock_request.overwrite_existing = False
        
        mock_progress = MagicMock()
        mock_stats = MagicMock()
        mock_file = MagicMock(spec=GitHubFile, path="path/to/file.txt")

        with patch('pathlib.Path.exists', return_value=True):
            result = await orchestrator._download_single_file(mock_file, mock_request, mock_progress, mock_stats)
            assert result is None
            download_service.save_content.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_single_file_saves_content(self, orchestrator, mock_services, mock_request):
        """Ensure file content is written via DownloadService.save_content."""
        github_service, download_service = mock_services
        github_service.get_file_content.return_value = b"hello world"
        mock_request.overwrite_existing = True
        
        mock_progress = MagicMock()
        mock_stats = MagicMock()
        mock_file = MagicMock(spec=GitHubFile, path="path/to/file.txt", download_url="http://fake.url/content")
        target_path = mock_request.destination / mock_file.path

        with patch('pathlib.Path.exists', return_value=False):
            await orchestrator._download_single_file(mock_file, mock_request, mock_progress, mock_stats)
            download_service.save_content.assert_awaited_once_with(
                b"hello world", target_path, show_progress=mock_request.show_progress_bars
            )

    # --- Control Methods Tests ---
    def test_cancel_sets_flag_and_logs(self, orchestrator):
        """Test cancel() -> sets _is_cancelled=True and logs."""
        with patch('forklet.core.orchestrator.logger') as mock_logger:
            orchestrator.cancel()
            assert orchestrator._is_cancelled is True
            mock_logger.info.assert_called_with("Download cancelled by user")

    @pytest.mark.asyncio
    async def test_pause_and_resume_run_without_errors(self, orchestrator):
        """Test that pause() and resume() run without errors."""
        try:
            await orchestrator.pause()
            await orchestrator.resume()
        except Exception as e:
            pytest.fail(f"pause() or resume() raised an exception: {e}")

    def test_get_current_progress_returns_none(self, orchestrator):
        """Test get_current_progress() -> returns None (until implemented)."""
        assert orchestrator.get_current_progress() is None