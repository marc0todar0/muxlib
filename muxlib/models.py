from dataclasses import dataclass, field


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
