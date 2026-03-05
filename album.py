import os
import re
from dataclasses import dataclass, field
from typing import Any

import yt_dlp
from pathvalidate import sanitize_filename

from single import SingleInfo, clean_title, clean_artist, build_ydl_opts


@dataclass
class AlbumInfo:
    title: str
    artist: str
    date: str
    thumbnail: str
    folder_name: str
    tracks: list[SingleInfo] = field(default_factory=list)
    track_urls: list[str] = field(default_factory=list)


def get_album_info(url: str) -> AlbumInfo:
    if "playlist" not in url:
        raise ValueError("get_album_info requires a playlist/album URL.")

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False) or {}  # type: ignore[reportAssignmentType]

    album_title: str = info.get("title") or "Unknown Album"
    album_title = re.sub(r"^album\s*-\s*", "", album_title, flags=re.IGNORECASE).strip()
    album_thumbnail: str = info.get("thumbnail") or ""
    album_date: str = ""

    entries = list(info.get("entries") or [])

    album_artist: str = info.get("uploader") or info.get("artist") or ""
    if not album_artist and entries:
        album_artist = entries[0].get("artist") or entries[0].get("uploader") or "Unknown"
    album_artist = clean_artist(album_artist or "Unknown")

    tracks: list[SingleInfo] = []
    track_urls: list[str] = []
    for entry in entries:
        title = clean_title(entry.get("track") or entry.get("title") or "Unknown")
        artist = clean_artist(entry.get("artist") or entry.get("uploader") or album_artist)
        thumbnail = entry.get("thumbnail") or album_thumbnail
        date = entry.get("release_date") or entry.get("upload_date") or ""
        tracknr = entry.get("playlist_index")

        if not album_date and date:
            album_date = date

        tracks.append(
            SingleInfo(
                title=title,
                artist=artist,
                thumbnail=thumbnail,
                date=date,
                album=album_title,
                filename=sanitize_filename(title),
                tracknr=tracknr,
            )
        )
        track_urls.append(entry.get("webpage_url") or entry.get("url") or "")

    return AlbumInfo(
        title=album_title,
        artist=album_artist,
        date=album_date,
        thumbnail=album_thumbnail,
        folder_name=sanitize_filename(album_title),
        tracks=tracks,
        track_urls=track_urls,
    )


def get_album(url: str, FOLDER: str = ".", EXT: str = "mp3") -> tuple[AlbumInfo, list[str]]:
    album_info = get_album_info(url)
    album_folder = os.path.join(FOLDER, album_info.folder_name)
    os.makedirs(album_folder, exist_ok=True)

    file_paths: list[str] = []
    for i, track in enumerate(album_info.tracks):
        track_url = album_info.track_urls[i]
        tracknr_str = f"{track.tracknr:02d}" if track.tracknr else f"{i + 1:02d}"
        final_path = os.path.join(album_folder, f"{tracknr_str} - {track.filename}")

        metadata = {
            "title": track.title,
            "album": track.album,
            "artist": track.artist,
            "date": track.date,
            "track": str(track.tracknr or i + 1),
        }
        ydl_opts = build_ydl_opts(ext=EXT, outtmpl=final_path, metadata=metadata)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
            ydl.download([track_url])

        file_path = f"{final_path}.{EXT}"
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"  [{tracknr_str}] {track.title} - {track.artist} [{file_size_mb:.2f} MB]")
        file_paths.append(file_path)

    print(f"\nAlbum downloaded: {album_info.title} ({len(file_paths)} tracks)")
    return album_info, file_paths
