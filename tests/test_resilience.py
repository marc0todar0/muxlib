"""Offline tests for the retry/cleanup behaviour around failed downloads."""
import os

import pytest
from yt_dlp.utils import DownloadError

from muxlib import downloader
from muxlib.downloader import MAX_RETRIES, describe_unavailable, is_retryable, with_retry
from muxlib.utils import remove_partial_files

FORBIDDEN = "ERROR: unable to download video data: HTTP Error 403: Forbidden"
AGE_GATED = (
    "ERROR: [youtube] TF3vpRFafkM: Sign in to confirm your age. Use --cookies-from-browser"
)


class TestIsRetryable:

    def test_403_is_retryable(self):
        assert is_retryable(Exception(FORBIDDEN))

    def test_age_gate_is_not_retryable(self):
        assert not is_retryable(Exception(AGE_GATED))

    def test_removed_video_is_not_retryable(self):
        assert not is_retryable(Exception("ERROR: Video unavailable"))

    def test_unknown_error_is_retryable(self):
        assert is_retryable(Exception("ERROR: connection reset by peer"))


class TestDescribeUnavailable:

    def test_age_gate_mentions_restriction(self):
        assert "Age-restricted" in describe_unavailable(Exception(AGE_GATED))

    def test_unknown_error_falls_back(self):
        assert describe_unavailable(Exception("something odd")).endswith("from YouTube.")


class TestRemovePartialFiles:

    def test_removes_leftovers_of_failed_track(self, tmp_path):
        final_path = tmp_path / "01 - Qua Giù"
        for name in ("01 - Qua Giù.webp", "01 - Qua Giù.part", "01 - Qua Giù"):
            (tmp_path / name).write_bytes(b"x")

        remove_partial_files(str(final_path))

        assert os.listdir(tmp_path) == []

    def test_keeps_other_tracks(self, tmp_path):
        (tmp_path / "01 - Qua Giù.webp").write_bytes(b"x")
        (tmp_path / "02 - Kontatto Pianeta.mp3").write_bytes(b"x")

        remove_partial_files(str(tmp_path / "01 - Qua Giù"))

        assert os.listdir(tmp_path) == ["02 - Kontatto Pianeta.mp3"]

    def test_missing_folder_is_a_noop(self, tmp_path):
        remove_partial_files(str(tmp_path / "nope" / "01 - Track"))


@pytest.fixture
def no_sleep(monkeypatch):
    """Keep the backoff from actually sleeping, and record what it asked for."""
    delays: list[float] = []
    monkeypatch.setattr(downloader.time, "sleep", delays.append)
    return delays


class TestWithRetry:

    def test_returns_result_on_first_success(self, no_sleep):
        result, error, attempts = with_retry(lambda: "ok", label="track")
        assert (result, error, attempts) == ("ok", None, 1)
        assert no_sleep == []

    def test_retries_until_success(self, no_sleep):
        calls = {"n": 0}

        def flaky() -> str:
            calls["n"] += 1
            if calls["n"] < 3:
                raise DownloadError(FORBIDDEN)
            return "ok"

        result, error, attempts = with_retry(flaky, label="track")
        assert (result, error, attempts) == ("ok", None, 3)
        assert no_sleep == [2, 4]  # exponential backoff between the two failures

    def test_gives_up_after_max_retries(self, no_sleep):
        def always_403() -> str:
            raise DownloadError(FORBIDDEN)

        result, error, attempts = with_retry(always_403, label="track")
        assert result is None
        assert isinstance(error, DownloadError)
        assert attempts == MAX_RETRIES
        assert len(no_sleep) == MAX_RETRIES - 1  # no sleep after the last attempt

    def test_permanent_error_stops_at_one_attempt(self, no_sleep):
        def age_gated() -> str:
            raise DownloadError(AGE_GATED)

        result, error, attempts = with_retry(age_gated, label="track")
        assert result is None
        assert isinstance(error, DownloadError)
        assert attempts == 1
        assert no_sleep == []
