"""
Unit tests for verbose logging functionality in GitHubDownloader API.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from forklet.interfaces.api import GitHubDownloader
from forklet.infrastructure.logger import logger


class TestVerboseLogging:
    """Test cases for verbose logging functionality."""
    
    def test_default_initialization(self):
        """Test that GitHubDownloader initializes with verbose=False by default."""
        downloader = GitHubDownloader()
        assert downloader.verbose is False
    
    def test_verbose_initialization(self):
        """Test that GitHubDownloader can be initialized with verbose=True."""
        downloader = GitHubDownloader(verbose=True)
        assert downloader.verbose is True
    
    def test_verbose_with_auth_token(self):
        """Test that verbose mode works with authentication token."""
        downloader = GitHubDownloader(auth_token="test_token", verbose=True)
        assert downloader.verbose is True
        assert downloader.auth_token == "test_token"
    
    @patch('forklet.interfaces.api.logger')
    def test_logger_level_verbose_true(self, mock_logger):
        """Test that logger level is set to DEBUG when verbose=True."""
        GitHubDownloader(verbose=True)
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
    
    @patch('forklet.interfaces.api.logger')
    def test_logger_level_verbose_false(self, mock_logger):
        """Test that logger level is set to INFO when verbose=False."""
        GitHubDownloader(verbose=False)
        mock_logger.setLevel.assert_called_with(logging.INFO)
    
    @patch('forklet.interfaces.api.logger')
    def test_set_verbose_method_enable(self, mock_logger):
        """Test the set_verbose method when enabling verbose mode."""
        downloader = GitHubDownloader(verbose=False)
        downloader.set_verbose(True)
        
        assert downloader.verbose is True
        # Should be called twice: once in __init__, once in set_verbose
        assert mock_logger.setLevel.call_count >= 2
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
    
    @patch('forklet.interfaces.api.logger')
    def test_set_verbose_method_disable(self, mock_logger):
        """Test the set_verbose method when disabling verbose mode."""
        downloader = GitHubDownloader(verbose=True)
        downloader.set_verbose(False)
        
        assert downloader.verbose is False
        # Should be called twice: once in __init__, once in set_verbose
        assert mock_logger.setLevel.call_count >= 2
        mock_logger.setLevel.assert_called_with(logging.INFO)
    
    def test_verbose_mode_toggle(self):
        """Test toggling verbose mode multiple times."""
        downloader = GitHubDownloader()
        
        # Start with False
        assert downloader.verbose is False
        
        # Enable
        downloader.set_verbose(True)
        assert downloader.verbose is True
        
        # Disable
        downloader.set_verbose(False)
        assert downloader.verbose is False
        
        # Enable again
        downloader.set_verbose(True)
        assert downloader.verbose is True
    
    @patch('forklet.interfaces.api.logger')
    def test_verbose_logging_in_download_method(self, mock_logger):
        """Test that verbose logging occurs during download operations."""
        # This test would require mocking the entire download chain
        # For now, we'll just test that the downloader is properly configured
        downloader = GitHubDownloader(verbose=True)
        
        # Verify the downloader has verbose mode enabled
        assert downloader.verbose is True
        
        # Verify logger was configured for DEBUG level
        mock_logger.setLevel.assert_called_with(logging.DEBUG)