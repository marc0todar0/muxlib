import os
import re
import yt_dlp  # require ffmpeg to work

# sudo apt install ffmpeg
# force reinstall yt-dlp
# pip install --upgrade --force-reinstall -r requirements.txt
from pathvalidate import sanitize_filename


class SingleInfo:
    def __init__(self, title, artist, thumbnail, date, album, filename, tracknr):
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
        info = ydl.extract_info(url, download=False)
        print(info)
        title = info.get("title", "output").strip()
        artist = info.get("artist") or info.get("uploader", "Unknown")
        thumbnail = info.get("thumbnail", "No thumbnail")
        upload_date = info.get("release_date", "")
    title = re.sub(
        r"\s*\((Visual|Official Video|Lyric Video|Audio|Official Audio)\)\s*",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    if "(Visual)" in title:
        title = title.replace("(Visual)", "").strip()

    # Converti virgole in punto e virgola per gli artisti
    if "," in artist:
        artist = artist.replace(",", ";")

    # if len(title) < 4 or len(title) > 15 or "-" in title or "," in title:
    #   user_input = input(f"Title: {title}\nAccept? [enter] or new title: ").strip()
    # title = title if user_input == "" else user_input
    title = title.strip()
    album = title
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


def get_single(url: str, FOLDER: str = ".", EXT: str = "mp3") -> tuple[str, str]:
    i = get_single_info(url=url)
    final_path = os.path.join(FOLDER, f"{i.filename}")
    ydl_opts = {
        "format": "bestaudio/best",
        "writethumbnail": True,
        #'embedthumbnail': True,
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
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    PATH = f"{final_path}.{EXT}"
    file_size_bytes = os.path.getsize(PATH)
    file_size_mb = file_size_bytes / (1024 * 1024)
    desc = f"""File saved: {PATH} [{file_size_mb:.2f} MB]
      Title: {i.title}
      Album: {i.album}
      Artist: {i.artist}
      Date: {i.date}
      Cover: {i.thumbnail}
    """
    print(desc)
    return desc, PATH


if __name__ == "__main__":
    url = "https://music.youtube.com/watch?v=dKXgUs2icDI"
    get_single(url)
