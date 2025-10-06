# tests/infrastructure/test_api.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from datetime import datetime

from forklet.interfaces.api import GitHubDownloader, DownloadConfig
from forklet.models import (
    RepositoryInfo, GitReference, DownloadResult, ProgressInfo,
    RepositoryType, DownloadStatus, DownloadRequest
)

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

# ---- Fixtures and Test Helpers ----

@pytest.fixture
def downloader():
    """
    Provides a GitHubDownloader instance with all dependencies mocked.
    Ensures tests do not hit the real network or GitHub API.
    """
    with patch("forklet.interfaces.api.GitHubAPIService") as mock_api, \
        patch("forklet.interfaces.api.DownloadOrchestrator") as mock_orch:
        
        # Mock async methods for services
        mock_api_instance = MagicMock()
        mock_api_instance.get_repository_info = AsyncMock()
        mock_api_instance.resolve_reference = AsyncMock()
        mock_api_instance.get_rate_limit_info = AsyncMock()
        mock_orch_instance = MagicMock()
        mock_orch_instance.execute_download = AsyncMock()
        mock_orch_instance.get_current_progress = AsyncMock()
        mock_api.return_value = mock_api_instance
        mock_orch.return_value = mock_orch_instance
        yield GitHubDownloader(auth_token="dummy")

def make_repo_info():
    """
    Returns a dummy RepositoryInfo instance for testing.
    """
    return RepositoryInfo(
        owner="me",
        name="repo",
        full_name="me/repo",
        url="https://github.com/me/repo",
        default_branch="main",
        repo_type=RepositoryType.PUBLIC,
        size=1024,
        is_private=False,
        is_fork=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        language="Python",
        description="Test repo"
    )

def make_git_ref():
    """
    Returns a dummy GitReference instance for testing.
    """
    return GitReference(
        name="main",
        ref_type="branch",
        sha="abc123"
    )

def make_progress():
    """
    Returns a dummy ProgressInfo instance for testing.
    """
    return ProgressInfo(
        total_files=1,
        downloaded_files=1,
        total_bytes=100,
        downloaded_bytes=100,
        current_file="README.md",
        download_speed=10.5,
        eta_seconds=2.0,
        started_at=datetime.now()
    )

def make_download_request():
    """
    Returns a dummy DownloadRequest instance for DownloadResult construction.
    """
    return DownloadRequest(
        repository=make_repo_info(),
        git_ref=make_git_ref(),
        destination=Path("/tmp"),
        strategy=DownloadStatus.COMPLETED
    )

## GitHubDownloader API Tests
# ------------------------------

async def test_get_repository_info_calls_service(downloader):
    """
    Ensure get_repository_info calls the GitHub service and returns RepositoryInfo.
    """
    repo_info = make_repo_info()
    downloader.github_service.get_repository_info = AsyncMock(return_value=repo_info)
    result = await downloader.get_repository_info("me", "repo")
    assert result == repo_info

async def test_resolve_reference_calls_service(downloader):
    """
    Ensure resolve_reference calls the GitHub service and returns GitReference.
    """
    ref = make_git_ref()
    downloader.github_service.resolve_reference = AsyncMock(return_value=ref)
    result = await downloader.resolve_reference("me", "repo", "main")
    assert result == ref

async def test_download_returns_download_result(downloader):
    """
    Simulate a download and check that a DownloadResult is returned.
    """
    download_result = DownloadResult(
        request=make_download_request(),
        status=DownloadStatus.COMPLETED,
        progress=make_progress()
    )
    # Mock dependencies for download flow
    downloader.github_service.get_repository_info = AsyncMock(return_value=make_repo_info())
    downloader.github_service.resolve_reference = AsyncMock(return_value=make_git_ref())
    downloader.orchestrator.execute_download = AsyncMock(return_value=download_result)
    result = await downloader.download("me", "repo", Path("/tmp"))
    assert isinstance(result, DownloadResult)

async def test_download_directory_applies_filters(downloader):
    """
    Simulate directory download and check that DownloadResult is returned.
    """
    download_result = DownloadResult(
        request=make_download_request(),
        status=DownloadStatus.COMPLETED,
        progress=make_progress()
    )
    downloader.github_service.get_repository_info = AsyncMock(return_value=make_repo_info())
    downloader.github_service.resolve_reference = AsyncMock(return_value=make_git_ref())
    downloader.orchestrator.execute_download = AsyncMock(return_value=download_result)
    result = await downloader.download_directory("me", "repo", "src/", Path("/tmp"))
    assert isinstance(result, DownloadResult)

async def test_download_file_targets_single_file(downloader):
    """
    Simulate single file download and check that DownloadResult is returned.
    """
    download_result = DownloadResult(
        request=make_download_request(),
        status=DownloadStatus.COMPLETED,
        progress=make_progress()
    )
    downloader.github_service.get_repository_info = AsyncMock(return_value=make_repo_info())
    downloader.github_service.resolve_reference = AsyncMock(return_value=make_git_ref())
    downloader.orchestrator.execute_download = AsyncMock(return_value=download_result)
    result = await downloader.download_file("me", "repo", "README.md", Path("/tmp"))
    assert isinstance(result, DownloadResult)

async def test_get_rate_limit_info_returns_details(downloader):
    """
    Ensure get_rate_limit_info returns with rate limit details.
    """
    downloader.github_service.get_rate_limit_info = AsyncMock(return_value={"limit": 5000, "remaining": 4999})
    info = await downloader.get_rate_limit_info()
    assert isinstance(info, dict)
    assert info == {"limit": 5000, "remaining": 4999}

async def test_get_download_progress_returns_progress_info(downloader):
    """
    Ensure get_download_progress returns a ProgressInfo object.
    """
    progress = make_progress()
    downloader.orchestrator.get_current_progress = AsyncMock(return_value=progress)
    result = await downloader.get_download_progress()
    assert isinstance(result, ProgressInfo)