import re
from datetime import datetime
from typing import Any

from mutagen import File as MutagenFile  # type: ignore[attr-defined]


def clean_title(title: str) -> str:
    return re.sub(r"\s*[\(\[].*?[\)\]]\s*", "", title).strip()


def split_artist_title(title: str) -> tuple[str, str] | None:
    """Split 'Artist - Title' format common in YouTube video titles.
    Returns (artist, title) or None if no separator found."""
    if " - " in title:
        artist, _, track = title.partition(" - ")
        artist = artist.strip()
        track = track.strip()
        if artist and track:
            return artist, track
    return None


def clean_artist(artist: str) -> str:
    parts = [p.strip() for p in re.split(r"[,;]", artist) if p.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return "; ".join(unique) if unique else artist


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
            {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
            {"key": "EmbedThumbnail"},
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
        ],
        "postprocessor_args": {
            "thumbnailsconvertor+ffmpeg_o": ["-vf", "crop=ih:ih"],
            "metadata+ffmpeg_o": [
                arg
                for key, val in metadata.items()
                for arg in ("-metadata", f"{key}={val}")
            ],
        },
        "outtmpl": outtmpl,
    }


def format_date(date: str) -> str:
    if not date:
        return ""
    return datetime.strptime(date, "%Y%m%d").strftime("%d/%m/%Y")


def artists_overlap(a: str, b: str) -> bool:
    set_a = {p.strip().lower() for p in re.split(r"[,;]", a) if p.strip()}
    set_b = {p.strip().lower() for p in re.split(r"[,;]", b) if p.strip()}
    return bool(set_a & set_b)


def read_artist_tag(file_path: str) -> str:
    audio = MutagenFile(file_path)
    if audio is None or not audio.tags:
        return ""
    for key in ("TPE1", "artist", "ARTIST", "\xa9ART"):
        if key in audio.tags:
            val = audio.tags[key]
            return "; ".join(str(x) for x in val) if isinstance(val, list) else str(val)
    return ""
