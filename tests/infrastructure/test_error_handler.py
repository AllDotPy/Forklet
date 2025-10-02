import pytest
import httpx

from types import SimpleNamespace

from forklet.infrastructure.error_handler import (
    DownloadError,
    RateLimitError,
    AuthenticationError,
    RepositoryNotFoundError,
    handle_api_error,
    retry_on_error,
)


# ---- Helpers ---------------------------------------------------------------

class FakeGithubException(Exception):
    def __init__(self, status: int, message: str = ""):
        super().__init__(message or f"status={status}")
        self.status = status


def raise_exc(exc: Exception):
    def _fn(*args, **kwargs):
        raise exc
    return _fn


# ---- Exception classes -----------------------------------------------------

def test_download_error_message_and_original():
    original = ValueError("boom")
    err = DownloadError("failed", original)
    assert err.message == "failed"
    assert err.original_error is original
    assert "failed" in str(err)
    assert "Original: boom" in str(err)


@pytest.mark.parametrize("exc_cls", [RateLimitError, AuthenticationError, RepositoryNotFoundError])
def test_specific_errors_store_message(exc_cls):
    err = exc_cls("msg")
    assert err.message == "msg"
    assert str(err) == "msg"


# ---- handle_api_error decorator -------------------------------------------

def test_handle_api_error_github_rate_limit(monkeypatch):
    from forklet.infrastructure import error_handler as eh
    monkeypatch.setattr(eh, "GithubException", FakeGithubException, raising=True)

    @handle_api_error
    def fn():
        raise FakeGithubException(403, "Rate limit exceeded")

    with pytest.raises(RateLimitError):
        fn()


@pytest.mark.parametrize("status, expected", [
    (401, AuthenticationError),
    (403, AuthenticationError),
])
def test_handle_api_error_github_authentication(monkeypatch, status, expected):
    from forklet.infrastructure import error_handler as eh
    monkeypatch.setattr(eh, "GithubException", FakeGithubException, raising=True)

    @handle_api_error
    def fn():
        raise FakeGithubException(status, "auth")

    with pytest.raises(expected):
        fn()


def test_handle_api_error_github_not_found(monkeypatch):
    from forklet.infrastructure import error_handler as eh
    monkeypatch.setattr(eh, "GithubException", FakeGithubException, raising=True)

    @handle_api_error
    def fn():
        raise FakeGithubException(404, "missing")

    with pytest.raises(RepositoryNotFoundError):
        fn()


def test_handle_api_error_github_other(monkeypatch):
    from forklet.infrastructure import error_handler as eh
    monkeypatch.setattr(eh, "GithubException", FakeGithubException, raising=True)

    @handle_api_error
    def fn():
        raise FakeGithubException(500, "oops")

    with pytest.raises(DownloadError):
        fn()


def test_handle_api_error_httpx_rate_limit():
    @handle_api_error
    def fn():
        raise httpx.RequestError("429 Too Many Requests")

    with pytest.raises(RateLimitError):
        fn()


def test_handle_api_error_httpx_other():
    @handle_api_error
    def fn():
        raise httpx.RequestError("conn reset")

    with pytest.raises(DownloadError):
        fn()


def test_handle_api_error_unexpected():
    @handle_api_error
    def fn():
        raise RuntimeError("boom")

    with pytest.raises(DownloadError):
        fn()


# ---- retry_on_error decorator ---------------------------------------------

def test_retry_on_error_retries_retryables(monkeypatch):
    calls = SimpleNamespace(n=0)

    @retry_on_error(max_retries=2)
    def fn():
        calls.n += 1
        if calls.n < 3:
            raise httpx.RequestError("temporary")
        return "ok"

    assert fn() == "ok"
    assert calls.n == 3


def test_retry_on_error_retries_on_rate_limit_error():
    calls = SimpleNamespace(n=0)

    @retry_on_error(max_retries=2)
    def fn():
        calls.n += 1
        if calls.n < 3:
            raise RateLimitError("hit rate limit")
        return "ok"

    assert fn() == "ok"
    assert calls.n == 3


def test_retry_on_error_retries_on_connection_error():
    calls = SimpleNamespace(n=0)

    @retry_on_error(max_retries=2)
    def fn():
        calls.n += 1
        if calls.n < 3:
            raise ConnectionError("network down")
        return "ok"

    assert fn() == "ok"
    assert calls.n == 3


def test_retry_on_error_stops_after_max_and_raises(monkeypatch):
    calls = SimpleNamespace(n=0)

    @retry_on_error(max_retries=2)
    def fn():
        calls.n += 1
        raise httpx.RequestError("still failing")

    with pytest.raises(httpx.RequestError):
        fn()
    assert calls.n == 3


def test_retry_on_error_does_not_retry_non_retryable():
    calls = SimpleNamespace(n=0)

    @retry_on_error(max_retries=5)
    def fn():
        calls.n += 1
        raise ValueError("no retry")

    with pytest.raises(ValueError):
        fn()
    assert calls.n == 1


