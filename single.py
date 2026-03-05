from __future__ import annotations

import os
import re
from typing import Any

import yt_dlp
from pathvalidate import sanitize_filename


class SingleInfo:
    def __init__(
        self,
        title: str,
        artist: str,
        thumbnail: str,
        date: str,
        album: str,
        filename: str,
        tracknr: int | None,
    ) -> None:
        self.title = title
        self.artist = artist
        self.thumbnail = thumbnail
        self.date = date
        self.album = album
        self.filename = filename
        self.tracknr = tracknr


def get_single_info(url: str) -> SingleInfo:
    if "playlist" in url:
        raise Exception(
            "get_single cannot download an album/playlist. Please use get_album/get_playlist"
        )
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False) or {}  # type: ignore[reportAssignmentType]
        metadata_keys = [
            "title", "track", "artist", "artists", "creator", "uploader",
            "album", "album_artist", "thumbnail", "release_date", "upload_date",
            "release_year", "description", "genre", "track_number",
        ]
        print("--- yt-dlp raw metadata ---")
        for k in metadata_keys:
            print(f"  {k}: {info.get(k)!r}")
        print("---")
        title: str = info.get("track") or info.get("title") or "output"
        artist: str = info.get("artist") or info.get("uploader") or "Unknown"
        thumbnail: str = info.get("thumbnail") or "No thumbnail"
        upload_date: str = info.get("release_date") or info.get("upload_date") or ""
    title = re.sub(r'\s*[\(\[].*?[\)\]]\s*', '', title).strip()
    if "," in artist:
        artist = artist.replace(",", ";")

    title = title.strip()
    album: str = info.get("album") or title
    safe_filename = sanitize_filename(title)
    return SingleInfo(
        title=title,
        artist=artist,
        thumbnail=thumbnail,
        date=upload_date,
        album=album,
        filename=safe_filename,
        tracknr=None,
    )


def get_single(url: str, FOLDER: str = ".", EXT: str = "mp3") -> str:
    i = get_single_info(url=url)
    final_path = os.path.join(FOLDER, f"{i.filename}")
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
            "-metadata",
            f"title={i.title}",
            "-metadata",
            f"album={i.album}",
            "-metadata",
            f"artist={i.artist}",
            "-metadata",
            f"date={i.date}",
        ],
        "outtmpl": final_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
        ydl.download([url])
    file_path = f"{final_path}.{EXT}"
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    desc = f"""File saved: {file_path} [{file_size_mb:.2f} MB]
      Title: {i.title}
      Album: {i.album}
      Artist: {i.artist}
      Date: {i.date}
      Cover: {i.thumbnail}
    """
    print(desc)
    return file_path


if __name__ == "__main__":
    url = "https://music.youtube.com/watch?v=dKXgUs2icDI"
    get_single(url)
