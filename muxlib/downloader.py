import os
import re
from typing import Any

import yt_dlp
from pathvalidate import sanitize_filename

from muxlib.models import AlbumInfo, SingleInfo
from muxlib.utils import build_ydl_opts, clean_artist, clean_title, split_artist_title


# --- Single ---


def get_single_info(url: str) -> SingleInfo:
    if "playlist" in url:
        raise ValueError(
            "get_single_info cannot handle a playlist URL. Use get_album_info instead."
        )
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False) or {}  # type: ignore[reportAssignmentType]

    raw_title = clean_title(info.get("track") or info.get("title") or "output")
    artist = info.get("artist") or ""

    # When track metadata is missing, try splitting "Artist - Title" from the video title
    if not info.get("track") and not artist:
        split = split_artist_title(raw_title)
        if split:
            artist, raw_title = split

    artist = clean_artist(artist or info.get("uploader") or "Unknown")
    title = raw_title
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


# --- Album / Playlist ---


def detect_is_album(info: dict[str, Any]) -> bool:
    title: str = info.get("title") or ""
    if re.match(r"^album\s*-\s*", title, flags=re.IGNORECASE):
        return True

    entries = list(info.get("entries") or [])
    if not entries:
        return False

    albums = [e.get("album") for e in entries if e.get("album", "").strip()]
    if len(albums) != len(entries) or len(set(albums)) != 1:
        return False
    return bool(albums[0] and albums[0].strip())


def get_album_info(url: str, force_album: bool | None = None) -> AlbumInfo:
    if "playlist" not in url:
        raise ValueError("get_album_info requires a playlist/album URL.")

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info: dict[str, Any] = ydl.extract_info(url, download=False) or {}  # type: ignore[reportAssignmentType]

    is_album = force_album if force_album is not None else detect_is_album(info)

    album_title: str = info.get("title") or "Unknown Album"
    if is_album:
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
        raw_title = clean_title(entry.get("track") or entry.get("title") or "Unknown")
        entry_artist = entry.get("artist") or ""

        if not entry.get("track") and not entry_artist:
            split = split_artist_title(raw_title)
            if split:
                entry_artist, raw_title = split

        title = raw_title
        artist = clean_artist(entry_artist or entry.get("uploader") or album_artist)
        thumbnail = entry.get("thumbnail") or album_thumbnail
        date = entry.get("release_date") or entry.get("upload_date") or ""
        tracknr = entry.get("playlist_index") if is_album else None

        if is_album:
            album = album_title
        else:
            album = entry.get("album") or clean_title(entry.get("track") or entry.get("title") or "Unknown")

        if not album_date and date:
            album_date = date

        tracks.append(
            SingleInfo(
                title=title,
                artist=artist,
                thumbnail=thumbnail,
                date=date,
                album=album,
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
        is_album=is_album,
        tracks=tracks,
        track_urls=track_urls,
    )


def get_album(url: str, FOLDER: str = ".", EXT: str = "mp3", force_album: bool | None = None) -> tuple[AlbumInfo, list[str]]:
    album_info = get_album_info(url, force_album=force_album)
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
        }
        if album_info.is_album:
            metadata["track"] = str(track.tracknr or i + 1)
        ydl_opts = build_ydl_opts(ext=EXT, outtmpl=final_path, metadata=metadata)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
            ydl.download([track_url])

        file_path = f"{final_path}.{EXT}"
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"  [{tracknr_str}] {track.title} - {track.artist} [{file_size_mb:.2f} MB]")
        file_paths.append(file_path)

    label = "Album" if album_info.is_album else "Playlist"
    print(f"\n{label} downloaded: {album_info.title} ({len(file_paths)} tracks)")
    return album_info, file_paths
