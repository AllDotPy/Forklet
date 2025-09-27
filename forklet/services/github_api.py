"""
Service for interacting with GitHub API with rate limiting and error handling.
"""

from typing import List, Optional, Dict, Any

import asyncio
import httpx
from github import Github, GithubException
# from github.Repository import Repository as GithubRepository

from ..infrastructure.rate_limiter import RateLimiter
from ..infrastructure.retry_manager import RetryManager
from ..infrastructure.error_handler import (
    handle_api_error, RateLimitError, 
    RepositoryNotFoundError, DownloadError
)
from ..models import (
    RepositoryInfo, GitReference, RepositoryType,
    GitHubFile
)
from ..models.constants import USER_AGENT

from forklet.infrastructure.logger import logger



####
##      GITHUB API SERVICE
#####
class GitHubAPIService:
    """
    Async service for interacting with GitHub API with comprehensive error handling.
    Focused solely on GitHub API interactions - no file system operations.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(
        self,
        rate_limiter: RateLimiter,
        retry_manager: RetryManager,
        auth_token: Optional[str] = None,
        timeout: int = 30
    ):
        self.rate_limiter = rate_limiter
        self.retry_manager = retry_manager
        self.auth_token = auth_token
        self.timeout = timeout
        
        # Configure HTTP client
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": USER_AGENT
        }
        
        if auth_token:
            headers["Authorization"] = f"token {auth_token}"
        
        self.http_client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(timeout)
        )
        
        # Sync client for PyGithub (used only for metadata)
        self.github_client = Github(auth_token) if auth_token else Github()
    
    async def __aenter__(self):
        """Async context manager entry."""

        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""

        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    @handle_api_error
    async def get_repository_info(
        self, 
        owner: str, 
        repo: str
    ) -> RepositoryInfo:
        """
        Get comprehensive information about a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            RepositoryInfo object with repository metadata
            
        Raises:
            RepositoryNotFoundError: If repository doesn't exist
            AuthenticationError: If authentication fails
        """

        try:
            # Use sync client for this operation as it's metadata-focused
            await self.rate_limiter.acquire()
            github_repo = await asyncio.to_thread(
                lambda: self.github_client.get_repo(f"{owner}/{repo}")
            )
            
            return RepositoryInfo(
                owner = owner,
                name = repo,
                full_name = github_repo.full_name,
                url = github_repo.html_url,
                default_branch = github_repo.default_branch,
                repo_type = RepositoryType.PRIVATE if github_repo.private else RepositoryType.PUBLIC,
                size = github_repo.size,
                is_private = github_repo.private,
                is_fork = github_repo.fork,
                created_at = github_repo.created_at,
                updated_at = github_repo.updated_at,
                language = github_repo.language,
                description = github_repo.description,
                topics = github_repo.get_topics()
            )
            
        except GithubException as e:
            if e.status == 404:
                raise RepositoryNotFoundError(
                    f"Repository {owner}/{repo} not found"
                )
            raise
    
    @handle_api_error
    async def resolve_reference(
        self, 
        owner: str, 
        repo: str, 
        ref: str
    ) -> GitReference:
        """
        Resolve a Git reference (branch, tag, or commit) to a specific commit SHA.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch name, tag name, or commit SHA
            
        Returns:
            GitReference object with resolved SHA
            
        Raises:
            ValueError: If reference cannot be resolved
        """

        try:
            # Try to get as branch first
            await self.rate_limiter.acquire()
            branch = await asyncio.to_thread(
                lambda: self.github_client.get_repo(f"{owner}/{repo}").get_branch(ref)
            )
            return GitReference(
                name = ref,
                ref_type = 'branch',
                sha = branch.commit.sha
            )
        except GithubException:
            pass  # Not a branch, try other types
        
        try:
            # Try to get as tag
            await self.rate_limiter.acquire()
            tags = await asyncio.to_thread(
                lambda: list(
                    self.github_client.get_repo(
                        f"{owner}/{repo}"
                    ).get_tags()
                )
            )
            for tag in tags:
                if tag.name == ref:
                    return GitReference(
                        name = ref,
                        ref_type = 'tag',
                        sha = tag.commit.sha
                    )
        except GithubException:
            pass  # Not a tag
        
        try:
            # Try to get as commit
            await self.rate_limiter.acquire()
            commit = await asyncio.to_thread(
                lambda: self.github_client.get_repo(
                    f"{owner}/{repo}"
                ).get_commit(ref)
            )
            return GitReference(
                name=ref,
                ref_type='commit',
                sha=commit.sha
            )
        except GithubException:
            pass  # Not a valid commit
        
        raise ValueError(
            f"Could not resolve reference '{ref}' for repository {owner}/{repo}"
        )
    
    @handle_api_error
    async def get_repository_tree(
        self,
        owner: str,
        repo: str,
        ref: GitReference,
        recursive: bool = True
    ) -> List[GitHubFile]:
        """
        Get the complete file tree for a repository at a specific reference.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: GitReference object
            recursive: Whether to get recursive tree
            
        Returns:
            List of GitHubFile objects
            
        Raises:
            RateLimitError: If rate limits are exceeded
        """

        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{ref.sha}"
        params = {"recursive": "1"} if recursive else {}
        
        try:
            await self.rate_limiter.acquire()
            response = await self.retry_manager.execute(
                lambda: self.http_client.get(url, params=params)
            )
            
            # Update rate limit info
            await self.rate_limiter.update_rate_limit_info(response.headers)
            
            response.raise_for_status()
            tree_data = response.json()
            
            files = []
            for item in tree_data.get("tree", []):

                # Only include files (blobs), not directories
                if item["type"] == "blob":
                    files.append(GitHubFile(
                        path = item["path"],
                        type = item["type"],
                        size = item.get("size", 0),
                        download_url = item.get("url"),
                        sha = item.get("sha"),
                        html_url = item.get("html_url")
                    ))
            
            return files
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise RateLimitError("GitHub API rate limit exceeded")
            raise
    
    @handle_api_error
    async def get_file_content(self, download_url: str) -> bytes:
        """
        Download file content from GitHub API.
        
        Args:
            download_url: GitHub API URL for the file content
            
        Returns:
            File content as bytes (already decoded from base64)
            
        Raises:
            DownloadError: If download fails
        """

        try:
            await self.rate_limiter.acquire()
            response = await self.retry_manager.execute(
                lambda: self.http_client.get(download_url)
            )
            
            response.raise_for_status()
            
            # GitHub API returns base64 encoded content
            content_data = response.json()
            if 'content' in content_data:
                import base64
                return base64.b64decode(content_data['content'])
            else:
                raise DownloadError(
                    f"No content found in API response for {download_url}"
                )
            
        except httpx.RequestError as e:
            raise DownloadError(
                f"Failed to download file from {download_url}: {e}"
            )
    
    @handle_api_error
    async def get_directory_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: GitReference
    ) -> List[GitHubFile]:
        """
        Get content of a specific directory.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Directory path
            ref: GitReference object
            
        Returns:
            List of GitHubFile objects in the directory
        """

        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref.sha}
        
        await self.rate_limiter.acquire()
        response = await self.retry_manager.execute(
            lambda: self.http_client.get(url, params=params)
        )
        
        response.raise_for_status()
        contents = response.json()
        
        files = []
        for item in contents:
            if item["type"] == "file":  # Only include files
                files.append(GitHubFile(
                    path = item["path"],
                    type = item["type"],
                    size = item.get("size", 0),
                    download_url = item.get("download_url"),
                    sha = item.get("sha"),
                    html_url = item.get("html_url")
                ))
        
        return files
    
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit information.
        
        Returns:
            Dictionary with rate limit information
        """

        url = f"{self.BASE_URL}/rate_limit"
        
        await self.rate_limiter.acquire()
        response = await self.retry_manager.execute(
            lambda: self.http_client.get(url)
        )
        
        response.raise_for_status()
        return response.json()
    
    async def test_connection(self) -> bool:
        """
        Test connection to GitHub API.
        
        Returns:
            True if connection is successful, False otherwise
        """

        try:
            await self.get_rate_limit_info()
            return True
        except Exception as e:
            logger.error(
                f"GitHub API connection test failed: {e}"
            )
            return False
