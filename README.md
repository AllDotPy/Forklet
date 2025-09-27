# Forklet

Download any file or folder from any GitHub repo by branch, tag, or commit with glob pattern filtering.

## Features

- ✅ Download entire repositories or specific files/folders
- ✅ Support for branches, tags, and specific commits
- ✅ Advanced filtering with glob patterns
- ✅ Rate limiting and intelligent retry mechanisms
- ✅ Concurrent downloads for better performance
- ✅ Both CLI and Python API interfaces
- ✅ Comprehensive error handling and logging
- ✅ Cache support for repeated downloads

## Installation

```bash
pip install forklet
```

Or from source
```bash
git clone https://github.com/AllDotPy/Forklet.git
cd forklet
pip install -e .
```

## CLI Usage

```bash
# Download entire repository
forklet download octocat/hello-world ./downloads

# Download specific branch
forklet download octocat/hello-world ./downloads --ref develop

# Download with filtering
forklet download octocat/hello-world ./downloads \
  --include "*.py" \
  --exclude "test_*" \
  --max-size 1000000

# Download with authentication
forklet download private-owner/private-repo ./downloads --token YOUR_GITHUB_TOKEN

# Show repository information
forklet info octocat/hello-world
```

## Python API Usage

```python
from forklet import GitHubDownloader
from pathlib import Path

# Initialize downloader
downloader = GitHubDownloader(auth_token="your_github_token")

# Download entire repository
result = await downloader.download(
    owner="octocat",
    repo="hello-world",
    destination=Path("./downloads"),
    ref="main",
    include_patterns=["*.py", "*.md"],
    exclude_patterns=["test_*"]
)

print(f"Downloaded {len(result.downloaded_files)} files")
print(f"Total size: {result.progress.downloaded_bytes} bytes")

# Download specific directory
result = await downloader.download_directory(
    owner="octocat",
    repo="hello-world",
    directory_path="src",
    destination=Path("./src-only")
)

# Download specific file
result = await downloader.download_file(
    owner="octocat",
    repo="hello-world",
    file_path="README.md",
    destination=Path("./readme.md")
)
```

<!-- ## Configuration

Set environment variables for configuration:

```bash
export GITHUB_TOKEN=your_github_token
export FORKLET_CONCURRENT_DOWNLOADS=10
export FORKLET_CACHE_ENABLED=true
export FORKLET_LOG_LEVEL=DEBUG
```

Or use a `.env` file:

```bash
GITHUB_TOKEN=your_github_token
FORKLET_CONCURRENT_DOWNLOADS=10
FORKLET_CACHE_ENABLED=true
FORKLET_LOG_LEVEL=DEBUG 
```-->

## 🤝 Contributing

We welcome contributions from the community! Please see the CONTRIBUTING.md guide for more information.

## License 📜

Apache-2.0 license  © 2025 AllDotPy
