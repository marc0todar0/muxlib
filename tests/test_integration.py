"""Integration test using a real NCS track from YouTube Music."""
import os

from single import get_single_info, get_single
from album import get_album_info, get_album

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


NCS_ALBUM_URL = "https://music.youtube.com/playlist?list=OLAK5uy_nlb6UMnOEn0LYiaH5B4pN2uWs46lIWYzk"


class TestGetAlbumInfo:

    def test_returns_valid_album_metadata(self):
        info = get_album_info(NCS_ALBUM_URL)
        assert info.title
        assert info.artist
        assert len(info.tracks) > 0

    def test_tracks_have_metadata(self):
        info = get_album_info(NCS_ALBUM_URL)
        for track in info.tracks:
            assert track.title
            assert track.artist
            assert track.filename
            assert track.tracknr is not None

    def test_track_titles_no_brackets(self):
        info = get_album_info(NCS_ALBUM_URL)
        for track in info.tracks:
            assert "[" not in track.title
            assert "(" not in track.title

    def test_track_artists_no_commas(self):
        info = get_album_info(NCS_ALBUM_URL)
        for track in info.tracks:
            assert "," not in track.artist


class TestGetAlbum:

    def test_downloads_album(self, tmp_path):
        info = get_album_info(NCS_ALBUM_URL)
        expected_count = len(info.tracks)

        album_info, file_paths = get_album(NCS_ALBUM_URL, FOLDER=str(tmp_path), EXT="mp3")
        album_folder = os.path.join(str(tmp_path), album_info.folder_name)
        assert os.path.isdir(album_folder)
        assert len(file_paths) == expected_count
        for fp in file_paths:
            assert os.path.exists(fp)
            assert fp.endswith(".mp3")
            assert os.path.getsize(fp) > 100_000
