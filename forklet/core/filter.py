# src/github_downloader/core/filter_engine.py
"""
Engine for filtering repository content based on flexible criteria.
"""

import fnmatch
import re
from pathlib import Path
from typing import List, Set, Optional
from dataclasses import dataclass

from ..models import GitHubFile, FilterCriteria


####
##      FILTER RESULT
#####
@dataclass
class FilterResult:
    """Result of filtering operation."""
    
    included_files: List[GitHubFile]
    excluded_files: List[GitHubFile]
    total_files: int
    filtered_files: int


####
##      FILTER ENGINE
#####
class FilterEngine:
    """
    Advanced filtering engine for repository content.
    
    Supports glob patterns, file size limits, extensions, and custom criteria.
    """
    
    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria
        self._compiled_include_patterns = self._compile_patterns(criteria.include_patterns)
        self._compiled_exclude_patterns = self._compile_patterns(criteria.exclude_patterns)
    
    def _compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        """
        Compile glob patterns to regex patterns for faster matching.
        
        Args:
            patterns: List of glob patterns
            
        Returns:
            List of compiled regex patterns
        """

        compiled = []
        for pattern in patterns:
            # Convert glob to regex
            regex_pattern = fnmatch.translate(pattern)
            compiled.append(re.compile(regex_pattern))

        return compiled
    
    def _matches_patterns(self, path: str, patterns: List[re.Pattern]) -> bool:
        """
        Check if path matches any of the compiled patterns.
        
        Args:
            path: Path to check
            patterns: Compiled regex patterns
            
        Returns:
            True if path matches any pattern
        """

        for pattern in patterns:
            if pattern.match(path):
                return True
            
        return False
    
    def should_include_file(self, file: GitHubFile) -> bool:
        """
        Determine if a file should be included based on filter criteria.
        
        Args:
            file: GitHubFile to check
            
        Returns:
            True if file should be included
        """

        # Check file type
        if file.type != 'file':
            return False
        
        # Check file size limits
        if (
            self.criteria.max_file_size 
            and file.size > self.criteria.max_file_size
        ):
            return False
        
        if (
            self.criteria.min_file_size 
            and file.size < self.criteria.min_file_size
        ):
            return False
        
        if any(
            path in file.download_url 
            for path in self.criteria.target_paths
        ):
            return True
        
        # Check path patterns
        return self.criteria.matches_path(file.path)
    
    def filter_files(self, files: List[GitHubFile]) -> FilterResult:
        """
        Filter list of files based on criteria.
        
        Args:
            files: List of GitHubFile objects to filter
            
        Returns:
            FilterResult with included and excluded files
        """

        included = []
        excluded = []
        
        for file in files:
            if self.should_include_file(file):
                included.append(file)
            else:
                excluded.append(file)
        
        return FilterResult(
            included_files = included,
            excluded_files = excluded,
            total_files = len(files),
            filtered_files = len(included)
        )
    
    def get_matching_paths(self, all_paths: List[str]) -> List[str]:
        """
        Get paths that match the filter criteria.
        
        Args:
            all_paths: List of all available paths
            
        Returns:
            List of matching paths
        """

        return [path for path in all_paths if self.criteria.matches_path(path)]
    
    def validate_criteria(self) -> List[str]:
        """
        Validate filter criteria and return any issues.
        
        Returns:
            List of validation errors, empty if valid
        """

        errors = []
        
        # Check for conflicting patterns
        include_set = set(self.criteria.include_patterns)
        exclude_set = set(self.criteria.exclude_patterns)
        conflicts = include_set.intersection(exclude_set)
        
        if conflicts:
            errors.append(
                f"Conflicting include/exclude patterns: {', '.join(conflicts)}"
            )
        
        # Check file size limits
        if (self.criteria.min_file_size is not None and 
            self.criteria.max_file_size is not None and
            self.criteria.min_file_size > self.criteria.max_file_size):
            errors.append(
                "Minimum file size cannot be greater than maximum file size"
            )
        
        # Check extension conflicts
        ext_conflicts = self.criteria.file_extensions.intersection(self.criteria.excluded_extensions)
        if ext_conflicts:
            errors.append(
                f"Conflicting file extensions: {', '.join(ext_conflicts)}"
            )
        
        return errors
    
    @classmethod
    def create_default_filters(cls) -> FilterCriteria:
        """
        Create default filter criteria that excludes common unwanted files.
        
        Returns:
            Default FilterCriteria
        """

        return FilterCriteria(
            exclude_patterns=[
                "*.git/*",
                "*.github/*",
                "*node_modules/*",
                "*__pycache__/*",
                "*.DS_Store",
                "*Thumbs.db",
                "*.log",
                "*.tmp",
                "*.temp"
            ],
            include_hidden=False,
            include_binary=False
        )
