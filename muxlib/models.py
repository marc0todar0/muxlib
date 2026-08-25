from dataclasses import dataclass, field


class TrackUnavailableError(Exception):
    """YouTube refuses to serve a track (age-gated, private, removed).

    Carries a message meant for the user, so callers can report it without
    dumping a yt-dlp traceback.
    """


@dataclass
class SingleInfo:
    title: str
    artist: str
    thumbnail: str
    date: str
    album: str
    filename: str
    tracknr: int | None


@dataclass
class AlbumInfo:
    title: str
    artist: str
    date: str
    thumbnail: str
    folder_name: str
    is_album: bool = True
    tracks: list[SingleInfo] = field(default_factory=list)
    track_urls: list[str] = field(default_factory=list)
    unavailable: int = 0
    # Filled in by get_album: one "[nn] Title - reason" line per skipped track.
    skipped: list[str] = field(default_factory=list)
