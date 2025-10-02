from forklet.core.filter import FilterEngine
from forklet.models import FilterCriteria, GitHubFile


def make_file(path: str, size: int = 100, file_type: str = 'blob') -> GitHubFile:
    """Helper function to build GithubFile instances for tests."""
    return GitHubFile(path=path, type=file_type, size=size)


def test_include_pattern_matches():
    """Scenario: Path matching with include_patterns"""
    criteria = FilterCriteria(include_patterns=['*.py'])
    assert criteria.matches_path('main.py') is True
    assert criteria.matches_path('README.md') is False


def test_exclude_pattern_blocks_path():
    """Scenario: Path exclusion with exclude_patterns"""
    criteria = FilterCriteria(exclude_patterns=['*.md'])
    assert criteria.matches_path('script.py') is True
    assert criteria.matches_path('docs/README.md') is False


def test_hidden_files_handling():
    """Scenario: Handling of hidden files (with include_hidden=True/False)"""
    hidden_path = '.github/workflows/ci.yml'
    visible_criteria = FilterCriteria(include_hidden=False)
    assert visible_criteria.matches_path(hidden_path) is False

    hidden_criteria = FilterCriteria(include_hidden=True)
    assert hidden_criteria.matches_path(hidden_path) is True


def test_file_extension_filters():
    """Scenario: File extension filtering (file_extensions and excluded_extensions)"""
    criteria = FilterCriteria(
        file_extensions={'.py'}, excluded_extensions={'.log'})
    assert criteria.matches_path('src/app.py') is True
    assert criteria.matches_path('src/app.txt') is False
    assert criteria.matches_path('logs/error.log') is False


def test_target_paths_enforcement():
    """Scenario: target_paths enforcement"""
    criteria = FilterCriteria(
        target_paths=['docs/'], include_patterns=['*.md'])
    assert criteria.matches_path('docs/guide.md') is True
    assert criteria.matches_path('src/guide.md') is False

    engine = FilterEngine(criteria)
    target_file = make_file('docs/guide.txt')
    off_target_file = make_file('src/guide.txt')

    assert engine.should_include_file(target_file) is True
    assert engine.should_include_file(off_target_file) is False


def test_combined_filters_in_engine():
    """Scenario: Combination of filters (include + exclude + size constraints)"""
    criteria = FilterCriteria(
        include_patterns=["src/*.py"],
        exclude_patterns=["*/test_*.py"],
        min_file_size=50,
        max_file_size=500,
        file_extensions={".py"},
    )
    engine = FilterEngine(criteria)

    files = [
        make_file("src/main.py", size=200),
        make_file("src/test_helper.py", size=200),
        make_file("src/small.py", size=10),
        make_file("src/large.py", size=600),
        make_file("src/docs/readme.md", size=100),
        make_file("src/utils/helper.py", size=300, file_type="tree"),
    ]

    result = engine.filter_files(files)

    assert [file.path for file in result.included_files] == ["src/main.py"]
    assert {file.path for file in result.excluded_files} == {
        "src/test_helper.py",
        "src/small.py",
        "src/large.py",
        "src/docs/readme.md",
        "src/utils/helper.py",
    }
    assert result.total_files == len(files)
    assert result.filtered_files == 1
