import os
import re
import time
from collections.abc import Callable
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError
from pathvalidate import sanitize_filename

from muxlib.models import AlbumInfo, SingleInfo, TrackUnavailableError
from muxlib.utils import (
    artists_overlap,
    build_ydl_opts,
    clean_artist,
    clean_title,
    read_artist_tag,
    remove_partial_files,
    split_artist_title,
)


MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2

# YouTube hands out 403s on the format URL under load; the same track usually
# downloads fine a few seconds later. These errors, on the other hand, are the
# server's final answer — retrying them only delays the skip.
PERMANENT_ERROR_PATTERNS = (
    "sign in to confirm your age",
    "video unavailable",
    "private video",
    "removed by the uploader",
    "members-only",
)


def is_retryable(error: Exception) -> bool:
    message = str(error).lower()
    return not any(pattern in message for pattern in PERMANENT_ERROR_PATTERNS)


def describe_unavailable(error: Exception) -> str:
    message = str(error).lower()
    if "sign in to confirm your age" in message:
        return "Age-restricted track: YouTube will not serve it without a signed-in session."
    if "private video" in message:
        return "This video is private."
    if "removed by the uploader" in message or "video unavailable" in message:
        return "This video is no longer available."
    return "This track could not be downloaded from YouTube."


def with_retry[T](action: Callable[[], T], label: str) -> tuple[T | None, Exception | None, int]:
    """Run a yt-dlp call, retrying transient failures with exponential backoff.

    Returns (result, error, attempts). On success error is None; on failure
    result is None and error is the DownloadError that ended the last attempt.
    Permanent errors (see PERMANENT_ERROR_PATTERNS) return after one attempt.
    """
    last_error: Exception | None = None
    attempt = 0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return action(), None, attempt
        except DownloadError as e:
            last_error = e
            if not is_retryable(e):
                print(f"{label} - not retryable ({e})")
                break
            if attempt < MAX_RETRIES:
                delay = BACKOFF_BASE_SECONDS * 2 ** (attempt - 1)
                print(
                    f"{label} - attempt {attempt}/{MAX_RETRIES} "
                    f"failed, retrying in {delay}s ({e})"
                )
                time.sleep(delay)
    return None, last_error, attempt


# --- Single ---


def get_single_info(url: str) -> SingleInfo:
    if "playlist" in url:
        raise ValueError(
            "get_single_info cannot handle a playlist URL. Use get_album_info instead."
        )

    def extract() -> dict[str, Any]:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            return ydl.extract_info(url, download=False) or {}  # type: ignore[reportReturnType]

    info, error, _ = with_retry(extract, label=url)
    if error is not None:
        raise TrackUnavailableError(describe_unavailable(error)) from error
    assert info is not None

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
    album: str = clean_title(info.get("album") or "") or title

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
    existing = f"{final_path}.{EXT}"
    if os.path.exists(existing):
        if artists_overlap(read_artist_tag(existing), i.artist):
            os.remove(existing)
        else:
            final_path = os.path.join(FOLDER, sanitize_filename(f"{i.title} - {i.artist}"))
    metadata = {"title": i.title, "album": i.album, "artist": i.artist, "date": i.date}
    ydl_opts = build_ydl_opts(ext=EXT, outtmpl=final_path, metadata=metadata)

    def download() -> None:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
            ydl.download([url])

    _, error, _ = with_retry(download, label=i.title)
    if error is not None:
        remove_partial_files(final_path)
        raise TrackUnavailableError(describe_unavailable(error)) from error

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

    # ignoreerrors keeps one unavailable track (age-gated, removed, geo-blocked) from
    # aborting the whole playlist: yt-dlp yields None for it and we drop it below.
    def extract() -> dict[str, Any]:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "ignoreerrors": True}) as ydl:
            return ydl.extract_info(url, download=False) or {}  # type: ignore[reportReturnType]

    info, error, _ = with_retry(extract, label=url)
    if error is not None:
        raise TrackUnavailableError(describe_unavailable(error)) from error
    assert info is not None

    raw_entries = list(info.get("entries") or [])
    info["entries"] = [e for e in raw_entries if e]
    unavailable = len(raw_entries) - len(info["entries"])

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
            album = clean_title(entry.get("album") or entry.get("track") or entry.get("title") or "Unknown")

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
        unavailable=unavailable,
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
            "album_artist": album_info.artist,
            "date": track.date,
        }
        if album_info.is_album:
            metadata["track"] = str(track.tracknr or i + 1)
        ydl_opts = build_ydl_opts(ext=EXT, outtmpl=final_path, metadata=metadata)

        label = f"  [{tracknr_str}] {track.title}"

        def download() -> None:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
                ydl.download([track_url])

        _, error, attempts = with_retry(download, label=label)
        if error is not None:
            remove_partial_files(final_path)
            reason = describe_unavailable(error)
            album_info.skipped.append(f"[{tracknr_str}] {track.title} - {reason}")
            print(f"{label} - SKIPPED after {attempts} attempt(s): {reason}")
            continue

        file_path = f"{final_path}.{EXT}"
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"  [{tracknr_str}] {track.title} - {track.artist} [{file_size_mb:.2f} MB]")
        file_paths.append(file_path)

    label = "Album" if album_info.is_album else "Playlist"
    print(f"\n{label} downloaded: {album_info.title} ({len(file_paths)} tracks)")
    if album_info.skipped:
        print(f"Skipped {len(album_info.skipped)} unavailable track(s):")
        for entry in album_info.skipped:
            print(f"  {entry}")
    if album_info.unavailable:
        print(f"Skipped {album_info.unavailable} track(s) that could not be read at all")
    return album_info, file_paths
