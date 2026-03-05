"""Integration test using a real NCS track from YouTube Music."""
import os

from single import get_single_info, get_single

NCS_URL = "https://music.youtube.com/watch?v=rgxfky2vqw4"


class TestGetSingleInfo:

    def test_returns_valid_metadata(self):
        info = get_single_info(NCS_URL)
        assert info.title
        assert info.artist
        assert info.filename
        assert info.thumbnail.startswith("http")
        assert len(info.date) == 8  # YYYYMMDD

    def test_title_has_no_brackets(self):
        info = get_single_info(NCS_URL)
        assert "[" not in info.title
        assert "(" not in info.title

    def test_artist_has_no_commas(self):
        info = get_single_info(NCS_URL)
        assert "," not in info.artist


class TestGetSingle:

    def test_downloads_mp3(self, tmp_path):
        file_path = get_single(NCS_URL, FOLDER=str(tmp_path), EXT="mp3")
        assert os.path.exists(file_path)
        assert file_path.endswith(".mp3")
        assert os.path.getsize(file_path) > 100_000
