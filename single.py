import os
import re
from dataclasses import dataclass
from typing import Any

import yt_dlp
from pathvalidate import sanitize_filename


@dataclass
class SingleInfo:
    title: str
    artist: str
    thumbnail: str
    date: str
    album: str
    filename: str
    tracknr: int | None


def clean_title(title: str) -> str:
    return re.sub(r"\s*[\(\[].*?[\)\]]\s*", "", title).strip()


def clean_artist(artist: str) -> str:
    if "," in artist:
        return artist.replace(",", ";")
    return artist


def build_ydl_opts(ext: str, outtmpl: str, metadata: dict[str, str]) -> dict[str, Any]:
    return {
        "format": "bestaudio/best",
        "writethumbnail": True,
        "quiet": False,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": ext,
                "preferredquality": "192",
            },
            {"key": "EmbedThumbnail"},
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
        ],
        "postprocessor_args": [
            arg
            for key, val in metadata.items()
            for arg in ("-metadata", f"{key}={val}")
        ],
        "outtmpl": outtmpl,
    }


def get_single_info(url: str) -> SingleInfo:
    if "playlist" in url:
        raise ValueError(
            "get_single_info cannot handle a playlist URL. Use get_album_info instead."
        )
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False) or {}  # type: ignore[reportAssignmentType]

    title = clean_title(info.get("track") or info.get("title") or "output")
    artist = clean_artist(info.get("artist") or info.get("uploader") or "Unknown")
    thumbnail: str = info.get("thumbnail") or ""
    date: str = info.get("release_date") or info.get("upload_date") or ""
    album: str = info.get("album") or title

    return SingleInfo(
        title=title,
        artist=artist,
        thumbnail=thumbnail,
        date=date,
        album=album,
        filename=sanitize_filename(title),
        tracknr=None,
    )


def get_single(url: str, FOLDER: str = ".", EXT: str = "mp3") -> str:
    i = get_single_info(url=url)
    final_path = os.path.join(FOLDER, i.filename)
    metadata = {"title": i.title, "album": i.album, "artist": i.artist, "date": i.date}
    ydl_opts = build_ydl_opts(ext=EXT, outtmpl=final_path, metadata=metadata)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
        ydl.download([url])

    file_path = f"{final_path}.{EXT}"
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Saved: {file_path} [{file_size_mb:.2f} MB] - {i.title} by {i.artist}")
    return file_path
