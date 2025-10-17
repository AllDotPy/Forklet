import asyncio
import pytest
from pathlib import Path
from datetime import datetime

from forklet.core.orchestrator import DownloadOrchestrator
from forklet.services.github_api import GitHubAPIService
from forklet.services.download import DownloadService
from forklet.infrastructure.retry_manager import RetryManager
from forklet.infrastructure.rate_limiter import RateLimiter
from forklet.models.github import GitHubFile
from forklet.models.download import DownloadRequest, FilterCriteria
from forklet.models.github import RepositoryInfo, GitReference, RepositoryType


@pytest.mark.asyncio
async def test_orchestrator_dry_run(tmp_path, monkeypatch):
    # Arrange: create mock files returned by GitHub API
    files = [
        GitHubFile(path="src/main.py", type="blob", size=100, download_url="https://api.github.com/file1"),
        GitHubFile(path="README.md", type="blob", size=50, download_url="https://api.github.com/file2"),
    ]

    async def mock_get_repository_tree(owner, repo, ref):
        return files

    # Setup services
    rate_limiter = RateLimiter()
    retry_manager = RetryManager()
    github_service = GitHubAPIService(rate_limiter, retry_manager)
    download_service = DownloadService(retry_manager)

    # Monkeypatch the github_service.get_repository_tree to return our files
    monkeypatch.setattr(github_service, 'get_repository_tree', mock_get_repository_tree)

    orchestrator = DownloadOrchestrator(github_service, download_service)

    # Create a fake repository and ref
    repo = RepositoryInfo(
        owner='test', name='repo', full_name='test/repo', url='https://github.com/test/repo',
        default_branch='main', repo_type=RepositoryType.PUBLIC, size=1,
        is_private=False, is_fork=False, created_at=datetime.now(), updated_at=datetime.now()
    )
    ref = GitReference(name='main', ref_type='branch', sha='abc')

    # Create destination and create one existing file to test skipped detection
    dest = tmp_path / "out"
    dest.mkdir()
    existing = dest / "README.md"
    existing.write_text("existing")

    request = DownloadRequest(
        repository=repo,
        git_ref=ref,
        destination=dest,
        strategy=None,
        filters=FilterCriteria(),
        dry_run=True
    )

    # Act
    result = await orchestrator.execute_download(request)

    # Assert
    assert result is not None
    assert result.progress.total_files == 2
    assert result.progress.total_bytes == 150
    # No files should be downloaded in dry-run
    assert result.downloaded_files == []
    # README.md should be reported as skipped
    assert "README.md" in result.skipped_files
