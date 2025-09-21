"""
Service for interacting with GitHub API with rate limiting and error handling.
"""

import logging
from typing import List, Optional, Dict, Any

# import requests
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


logger = logging.getLogger(__name__)


####
##      GITHUB API SERVICE
#####
class GitHubAPIService:
    """
    Service for interacting with GitHub API with comprehensive error handling.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(
        self,
        rate_limiter: RateLimiter,
        retry_manager: RetryManager,
        auth_token: Optional[str] = None
    ):
        self.rate_limiter = rate_limiter
        self.retry_manager = retry_manager
        self.auth_token = auth_token
        self.github_client = Github(auth_token) if auth_token else Github()
        self.http_client = httpx.Client()
        
        if auth_token:
            self.http_client.headers.update({
                "Authorization": f"token {auth_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": USER_AGENT
            })
        else:
            self.http_client.headers.update({
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": USER_AGENT
            })
    
    @handle_api_error
    def get_repository_info(self, owner: str, repo: str) -> RepositoryInfo:
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
            with self.rate_limiter:
                github_repo = self.retry_manager.execute(
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
    def resolve_reference(
        self, 
        owner: str, 
        repo: str, ref: str
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
            with self.rate_limiter:
                branch = self.retry_manager.execute(
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
            with self.rate_limiter:
                tags = self.retry_manager.execute(
                    lambda: self.github_client.get_repo(f"{owner}/{repo}").get_tags()
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
            with self.rate_limiter:
                commit = self.retry_manager.execute(
                    lambda: self.github_client.get_repo(
                        f"{owner}/{repo}"
                    ).get_commit(ref)
                )
                return GitReference(
                    name = ref,
                    ref_type = 'commit',
                    sha = commit.sha
                )
        except GithubException:
            pass  # Not a valid commit
        
        raise ValueError(
            f"Could not resolve reference '{ref}' for repository {owner}/{repo}"
        )
    
    @handle_api_error
    def get_repository_tree(
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
            with self.rate_limiter:
                response: httpx.Response = self.retry_manager.execute(
                    lambda: self.http_client.get(url, params=params, timeout=30)
                )
            
            # Update rate limit info
            self.rate_limiter.update_rate_limit_info(response.headers)
            
            response.raise_for_status()
            tree_data = response.json()
            
            files = []
            for item in tree_data.get("tree", []):
                files.append(GitHubFile(
                    path = item["path"],
                    type = item["type"],
                    size = item.get("size", 0),
                    download_url = item.get("url"),
                    sha = item.get("sha"),
                    html_url = item.get("html_url")
                ))
            
            return files
            
        except httpx.HTTPError as e:
            if '403' in str(e):
                raise RateLimitError("GitHub API rate limit exceeded")
            raise
    
    @handle_api_error
    def get_file_content(self, download_url: str) -> bytes:
        """
        Download file content from GitHub.
        
        Args:
            download_url: Direct download URL for the file
            
        Returns:
            File content as bytes
            
        Raises:
            DownloadError: If download fails
        """

        try:
            with self.rate_limiter:
                response: httpx.Response = self.retry_manager.execute(
                    lambda: self.http_client.get(download_url, timeout=30)
                )
            
            response.raise_for_status()
            return response.content
            
        except httpx.RequestError as e:
            raise DownloadError(
                f"Failed to download file from {download_url}: {e}"
            )
    
    @handle_api_error
    def get_directory_content(
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
        
        with self.rate_limiter:
            response: httpx.Response = self.retry_manager.execute(
                lambda: self.http_client.get(url, params=params, timeout=30)
            )
        
        response.raise_for_status()
        contents = response.json()
        
        files = []
        for item in contents:
            files.append(GitHubFile(
                path = item["path"],
                type = item["type"],
                size = item.get("size", 0),
                download_url = item.get("download_url"),
                sha = item.get("sha"),
                html_url = item.get("html_url")
            ))
        
        return files
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit information.
        
        Returns:
            Dictionary with rate limit information
        """

        url = f"{self.BASE_URL}/rate_limit"
        
        with self.rate_limiter:
            response: httpx.Response = self.retry_manager.execute(
                lambda: self.http_client.get(url, timeout=10)
            )
        
        response.raise_for_status()
        return response.json()
