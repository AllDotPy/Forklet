# Forklet Improvement Plan

## Overview
This plan outlines a structured approach to improve Forklet's codebase while maintaining backward compatibility and ensuring all tests pass at each stage.

## Prerequisites
- Virtual environment activated: `source .venv/bin/activate`
- All tests passing: `python -m pytest tests/ -v`

## Phase 1: Orchestrator Refactoring (Current Branch)
**Branch**: `feature/refactor-orchestrator`
**Goal**: Split the monolithic `DownloadOrchestrator` into smaller, focused components

### Tasks:
1. **Extract Concurrency Manager**
   - Create `concurrency_manager.py` handling semaphore logic and task management
   - Move `_download_files_concurrently` and related methods

2. **Extract Progress Tracker**
   - Create `progress_tracker.py` managing progress updates and state
   - Move progress update logic and file tracking

3. **Extract State Controller**
   - Create `state_controller.py` handling pause/resume/cancel logic
   - Move event management and state flags

4. **Refactor Main Orchestrator**
   - Keep only high-level orchestration logic
   - Depend on the new specialized components
   - Maintain identical public interface

### Verification:
- Run all tests: `python -m pytest tests/ -v`
- Manual testing of download operations with pause/resume/cancel
- Verify no functional changes

### Commit Strategy:
- `feat(concurrency): extract concurrency management`
- `feat(progress): extract progress tracking`
- `feat(state): extract state controller`
- `refactor(orchestrator): simplify main class using new components`

## Phase 2: Reference Resolution Improvement
**Branch**: `feature/refactor-reference-resolution`
**Goal**: Eliminate code duplication in `GitHubAPIService.resolve_reference()`

### Tasks:
1. **Create Reference Resolution Helper**
   - Extract common logic into `_try_reference_type()` method
   - Use iterable of reference types with corresponding GitHub API calls

2. **Simplify Main Method**
   - Replace repetitive try/except blocks with loop
   - Maintain identical error handling and return values

### Verification:
- Run API-related tests: `python -m pytest tests/infrastructure/test_github_api.py -v`
- Test with various reference types (branch, tag, commit)
- Verify error cases still work correctly

### Commit Strategy:
- `refactor(github-api): extract reference resolution helper`
- `refactor(github-api): simplify resolve_reference using helper`

## Phase 3: Streaming Download Implementation
**Branch**: `feature/streaming-downloads`
**Goal**: Reduce memory footprint for large file downloads

### Tasks:
1. **Add Streaming Threshold Configuration**
   - Add `stream_threshold` parameter to `DownloadRequest` (default: 10MB)
   - Update constructor validation

2. **Modify Download Service**
   - Update `save_content()` to accept streaming option
   - Implement chunked writing for large files
   - Keep existing behavior for small files

3. **Update GitHub API Service**
   - Modify `get_file_content()` to return streaming response when appropriate
   - Add parameter to control download method

### Verification:
- Run download-related tests
- Test with files both below and above threshold
- Monitor memory usage during large file downloads
- Verify file integrity remains intact

### Commit Strategy:
- `feat(download): add streaming threshold config`
- `feat(download-service): implement streaming write`
- `feat(github-api): support streaming file content`

## Phase 4: Enhanced Rate Limiting
**Branch**: `feature/enhanced-rate-limiting`
**Goal**: Improve rate limit handling with dynamic adjustments

### Tasks:
1. **Add Dynamic Concurrency Adjustment**
   - Monitor remaining rate limit headers
   - Automatically adjust semaphore limits based on availability
   - Implement conservative backoff when limits are low

2. **Improve Exhaustion Handling**
   - Add predictive waiting before exhaustion
   - Implement queue pausing/resuming based on limit recovery
   - Add better logging for rate limit events

### Verification:
- Run rate limiter tests: `python -m pytest tests/infrastructure/test_rate_limiter.py -v`
- Simulate rate limit scenarios (manually or with mocking)
- Verify graceful degradation under limits
- Test recovery when limits reset

### Commit Strategy:
- `feat(rate-limiter): add dynamic concurrency adjustment`
- `feat(rate-limiter): improve exhaustion prediction`
- `feat(github-api): integrate dynamic limiting`

## Phase 5: Integrity Checking
**Branch**: `feature/integrity-checking`
**Goal**: Add optional verification of downloaded file integrity

### Tasks:
1. **Add Verification Options**
   - Add `verify_integrity` boolean to `DownloadRequest`
   - Add `verification_method` enum (SHA256, size, none)
   - Default to disabled for backward compatibility

2. **Implement Verification Logic**
   - After file download, compute hash/size
   - Compare with expected values from GitHub API
   - Fail download if mismatch and retry if configured
   - Add verification statistics to results

### Verification:
- Run download tests with verification enabled/disabled
- Test with corrupted files (simulate network issues)
- Verify performance impact is minimal for small files
- Ensure large files still work with streaming

### Commit Strategy:
- `feat(request): add integrity verification options`
- `feat(download-service): implement verification logic`
- `feat(orchestrator): integrate verification step`

## Phase 6: Cache System Implementation
**Branch**: `feature/cache-implementation`
**Goal**: Fully implement the caching mechanism mentioned in features

### Tasks:
1. **Design Cache System**
   - Define what to cache (repository trees, file metadata)
   - Set expiration policies (time-based, access-based)
   - Choose storage location (disk cache in user cache dir)

2. **Implement Cache Manager**
   - Create `cache_manager.py` with get/set/delete operations
   - Add cache statistics tracking
   - Implement cache cleanup policies

3. **Integrate with Services**
   - Modify `GitHubAPIService` to use cache for tree requests
   - Add cache-busting options for forced refresh
   - Expose cache statistics in progress/results

### Verification:
- Run tests to ensure caching doesn't break functionality
- Measure performance improvement on repeated requests
- Verify cache expiration works correctly
- Test cache persistence between runs

### Commit Strategy:
- `feat(cache): implement cache manager`
- `feat(github-api): integrate caching for tree requests`
- `feat(cache): add cache statistics and management`

## Phase 7: CLI Validation Enhancement
**Branch**: `feature/cli-validation`
**Goal**: Improve parameter validation and error messages in CLI

### Tasks:
1. **Add Cross-Parameter Validation**
   - Validate min-size ≤ max-size
   - Check extension conflicts (included vs excluded)
   - Verify path patterns are valid globs
   - Ensure concurrent downloads > 0

2. **Improve Error Messages**
   - Provide specific, actionable feedback
   - Show invalid values and constraints
   - Suggest corrections when possible

3. **Add Custom Click Validators**
   - Create reusable validation decorators
   - Apply to relevant options and arguments

### Verification:
- Run CLI tests: `python -m pytest tests/cli/ -v`
- Test various invalid parameter combinations
- Verify helpful error messages appear
- Ensure valid combinations still work correctly

### Commit Strategy:
- `feat(validation): add cross-parameter checks`
- `feat(cli): improve error messaging`
- `feat(click): add custom validators`

## Phase 8: Detailed Error Logging
**Branch**: `feature/detailed-error-logging`
**Goal**: Enhance error context for easier debugging

### Tasks:
1. **Enrich Error Information**
   - Include request ID, file path, URL in error logs
   - Add HTTP status codes and response headers when available
   - Preserve original exception context

2. **Structured Error Logging**
   - Use consistent error format across modules
   - Add correlation IDs for tracing related operations
   - Log at appropriate levels (DEBUG for details, ERROR for failures)

3. **Error Aggregation**
   - Collect and summarize errors in batch operations
   - Provide error rates and patterns in final reports

### Verification:
- Run tests to ensure logging doesn't break functionality
- Trigger various error conditions and verify log content
- Check that sensitive data (tokens) is not logged
- Verify performance impact is negligible

### Commit Strategy:
- `feat(logging): enrich error context`
- `feat(logging): implement structured error format`
- `feat(logging): add error aggregation`

## Phase 9: HTTP Client Consolidation Evaluation
**Branch**: `feature/http-client-eval`
**Goal**: Evaluate and potentially reduce dependency duplication

### Tasks:
1. **Analyze Current Usage**
   - Map where httpx vs PyGithub is used
   - Identify overlapping functionality
   - Measure performance differences

2. **Prototype Consolidation**
   - Attempt to replace PyGithub calls with httpx where appropriate
   - Maintain compatibility with GitHub API features
   - Evaluate complexity vs benefit

3. **Decision and Implementation**
   - Based on evaluation, either:
     a) Consolidate to single client where beneficial
     b) Document clear separation of concerns
     c) Keep current approach if benefits don't outweigh costs

### Verification:
- Run all tests to ensure no regression
- Benchmark API call performance
- Verify GitHub API compliance
- Check dependency impact

### Commit Strategy:
- `doc(http-client): analyze current usage`
- `feat(http-client): prototype consolidation`
- `decision(http-client): document approach`

## Phase 10: Git Submodule Support
**Branch**: `feature/submodule-support`
**Goal**: Add optional recursive submodule processing

### Tasks:
1. **Add Submodule Options**
   - Add `recurse_submodules` boolean to `DownloadRequest`
   - Add `submodule_depth` limit for recursion prevention
   - Default to disabled for backward compatibility

2. **Implement Submodule Processing**
   - Detect `.gitmodules` file in repository tree
   - Parse submodule configuration (path, URL, branch)
   - Recursively process submodules as separate downloads
   - Maintain directory structure in destination

3. **Handle Edge Cases**
   - Detached HEAD states in submodules
   - Submodule authentication (inherit or separate tokens)
   - Circular dependency prevention
   - Failed submodule recovery options

### Verification:
- Run existing tests to ensure no regression
- Test with repositories containing submodules
- Verify recursive processing works correctly
- Test error handling in submodule chains
- Confirm performance impact when feature unused

### Commit Strategy:
- `feat(request): add submodule options`
- `feat(orchestrator): add submodule detection`
- `feat(download-service): implement submodule processing`
- `feat(orchestrator): handle submodule recursion`

## General Guidelines for Each Phase

### Before Starting:
1. Ensure current branch is up to date with main
2. Create new descriptive branch from main
3. Verify all tests pass on baseline

### During Development:
1. Make small, focused commits (ideally one logical change per commit)
2. Run relevant test subsets frequently
3. Run full test suite before moving to next phase
4. Document any non-obvious decisions in commit messages

### After Completion:
1. Run full test suite: `python -m pytest tests/ -v`
2. Perform manual sanity checks for key features
3. Push branch and create pull request for review
4. Only merge to main after approval and successful CI

### Example Workflow:
```bash
# Start new phase
git checkout main
git pull
git checkout -b feature/phase-name

# Work: make changes, test, commit
git add .
git commit -m "feat(component): description"

# Regular verification
python -m pytest tests/specific_subset.py -v

# End phase
git push origin feature/phase-name
# Create PR, get approval, merge
```

## Definition of Done for Each Phase
- [ ] All existing tests pass
- [ ] New functionality tested (unit and manual)
- [ ] No performance regressions (>5% slower for equivalent operations)
- [ ] Memory usage improved or maintained
- [ ] Documentation updated if needed (README, docstrings)
- [ ] Branch ready for pull request

## Safety Measures
- Always maintain backward compatibility
- Feature flags for major changes when appropriate
- Comprehensive testing before merging
- Ability to rollback via git if issues discovered post-merge

Let's begin with Phase 1 on your current branch.