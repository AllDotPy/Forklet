import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the necessary components from the application code
from forklet.core.orchestrator import DownloadOrchestrator
from forklet.services import GitHubAPIService, DownloadService
from forklet.models import DownloadStatus, GitHubFile, DownloadRequest

# Because the code we are testing uses 'async', we use IsolatedAsyncioTestCase
class TestDownloadOrchestrator(unittest.IsolatedAsyncioTestCase):

    # --- Test Case 1 ---
    async def test_initialization(self):
        """
        Tests that the DownloadOrchestrator class initializes correctly.
        """
        print("-> Running: test_initialization...")

        # ARRANGE
        mock_github_service = AsyncMock(spec=GitHubAPIService)
        mock_download_service = AsyncMock(spec=DownloadService)
        test_max_downloads = 5

        # ACT
        orchestrator = DownloadOrchestrator(
            github_service=mock_github_service,
            download_service=mock_download_service,
            max_concurrent_downloads=test_max_downloads
        )

        # ASSERT
        self.assertIs(orchestrator.github_service, mock_github_service)
        self.assertIs(orchestrator.download_service, mock_download_service)
        self.assertEqual(orchestrator.max_concurrent_downloads, test_max_downloads)
        self.assertIsNotNone(orchestrator._semaphore)
        self.assertEqual(orchestrator._semaphore._value, test_max_downloads)
        
        print("... PASSED")

    # --- Test Case 2 ---
    async def test_execute_download_handles_success(self):
        """
        Tests the successful, happy-path flow for the execute_download method.
        """
        print("-> Running: test_execute_download_handles_success...")

        # ARRANGE
        mock_github_service = AsyncMock(spec=GitHubAPIService)
        mock_download_service = AsyncMock(spec=DownloadService)
        
        # Create fake file data
        fake_files = [
            MagicMock(spec=GitHubFile, path="src/main.py", size=1024, type="file"),
            MagicMock(spec=GitHubFile, path="README.md", size=512, type="file"),
        ]
        mock_github_service.get_repository_tree.return_value = fake_files
        
        # Create a fake download request object
        mock_request = MagicMock(spec=DownloadRequest)
        mock_filters = MagicMock()
        mock_filters.include_patterns = []
        mock_filters.exclude_patterns = []
        mock_request.filters = mock_filters
        mock_request.create_destination = False
        mock_repo = MagicMock()
        mock_repo.display_name = "test/repo"
        mock_request.repository = mock_repo
        mock_request.git_ref = "main"

        # THIS IS THE LINE I HAVE CORRECTED:
        orchestrator = DownloadOrchestrator(
            github_service=mock_github_service,
            download_service=mock_download_service,
        )
        
        # Temporarily replace the internal download method
        with patch.object(orchestrator, '_download_files_concurrently', return_value=(["src/main.py", "README.md"], {})) as mock_download_method:
        
            # ACT
            result = await orchestrator.execute_download(mock_request)

            # ASSERT
            mock_github_service.get_repository_tree.assert_awaited_once()
            mock_download_method.assert_awaited_once()
            self.assertEqual(result.status, DownloadStatus.COMPLETED)
            self.assertEqual(len(result.downloaded_files), 2)
        
        print("... PASSED")

# This part allows the test file to be run directly
if __name__ == '__main__':
    unittest.main()