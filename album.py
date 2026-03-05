import os
import re
from typing import Any

import yt_dlp
from pathvalidate import sanitize_filename

from single import SingleInfo


class AlbumInfo:
    def __init__(
        self,
        title: str,
        artist: str,
        date: str,
        thumbnail: str,
        tracks: list[SingleInfo],
        folder_name: str,
    ) -> None:
        self.title = title
        self.artist = artist
        self.date = date
        self.thumbnail = thumbnail
        self.tracks = tracks
        self.folder_name = folder_name


def _clean_title(title: str) -> str:
    return re.sub(r"\s*[\(\[].*?[\)\]]\s*", "", title).strip()


def _clean_artist(artist: str) -> str:
    if "," in artist:
        return artist.replace(",", ";")
    return artist


def get_album_info(url: str) -> AlbumInfo:
    if "playlist" not in url:
        raise Exception(
            "get_album_info requires a playlist/album URL."
        )
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False) or {}  # type: ignore[reportAssignmentType]

    album_title: str = info.get("title") or "Unknown Album"
    album_title = re.sub(r"^album\s*-\s*", "", album_title, flags=re.IGNORECASE).strip()
    album_artist: str = info.get("uploader") or info.get("artist") or ""
    album_thumbnail: str = info.get("thumbnail") or ""
    album_date: str = ""

    entries = list(info.get("entries") or [])

    if not album_artist and entries:
        album_artist = entries[0].get("artist") or entries[0].get("uploader") or "Unknown"
    album_artist = album_artist or "Unknown"
    album_artist = _clean_artist(album_artist)
    tracks: list[SingleInfo] = []
    for entry in entries:
        title = entry.get("track") or entry.get("title") or "Unknown"
        title = _clean_title(title)
        artist = entry.get("artist") or entry.get("uploader") or album_artist
        artist = _clean_artist(artist)
        thumbnail = entry.get("thumbnail") or album_thumbnail
        date = entry.get("release_date") or entry.get("upload_date") or ""
        tracknr = entry.get("playlist_index")
        album = album_title
        safe_filename = sanitize_filename(title)

        if not album_date and date:
            album_date = date

        tracks.append(
            SingleInfo(
                title=title,
                artist=artist,
                thumbnail=thumbnail,
                date=date,
                album=album,
                filename=safe_filename,
                tracknr=tracknr,
            )
        )

    return AlbumInfo(
        title=album_title,
        artist=album_artist,
        date=album_date,
        thumbnail=album_thumbnail,
        tracks=tracks,
        folder_name=sanitize_filename(album_title),
    )


def get_album(url: str, FOLDER: str = ".", EXT: str = "mp3") -> tuple[AlbumInfo, list[str]]:
    album_info = get_album_info(url)
    album_folder = os.path.join(FOLDER, album_info.folder_name)
    os.makedirs(album_folder, exist_ok=True)

    entries = list(
        yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True})
        .extract_info(url, download=False)  # type: ignore[union-attr]
        .get("entries", [])
    )

    file_paths: list[str] = []
    for i, track in enumerate(album_info.tracks):
        entry = entries[i]
        track_url = entry.get("webpage_url") or entry.get("url") or ""
        tracknr_str = f"{track.tracknr:02d}" if track.tracknr else f"{i + 1:02d}"
        final_path = os.path.join(album_folder, f"{tracknr_str} - {track.filename}")

        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "writethumbnail": True,
            "quiet": False,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": EXT,
                    "preferredquality": "192",
                },
                {
                    "key": "EmbedThumbnail",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "postprocessor_args": [
                "-metadata", f"title={track.title}",
                "-metadata", f"album={track.album}",
                "-metadata", f"artist={track.artist}",
                "-metadata", f"date={track.date}",
                "-metadata", f"track={track.tracknr or i + 1}",
            ],
            "outtmpl": final_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
            ydl.download([track_url])

        file_path = f"{final_path}.{EXT}"
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"  [{tracknr_str}] {track.title} - {track.artist} [{file_size_mb:.2f} MB]")
        file_paths.append(file_path)

    print(f"\nAlbum downloaded: {album_info.title} ({len(file_paths)} tracks)")
    return album_info, file_paths
