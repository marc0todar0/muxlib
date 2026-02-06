import os
import re
import yt_dlp  # require ffmpeg to work

# sudo apt install ffmpeg
# force reinstall yt-dlp
# pip install --upgrade --force-reinstall -r requirements.txt
from pathvalidate import sanitize_filename


def get_single(url: str, FOLDER: str = ".", EXT: str = "mp3") -> tuple[str, str]:
    if "playlist" in url:
        raise Exception(
            "get_single cannot download an album/playlist. Please use get_album/get_playlist"
        )
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "output").strip()
        artist = info.get("artist") or info.get("uploader", "Unknown")
        thumbnail = info.get("thumbnail", "No thumbnail")
        upload_date = info.get("upload_date", "")
    title = re.sub(
        r"\s*\((Visual|Official Video|Lyric Video|Audio|Official Audio)\)\s*",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    # if len(title) < 4 or len(title) > 15 or "-" in title or "," in title:
    #   user_input = input(f"Title: {title}\nAccept? [enter] or new title: ").strip()
    # title = title if user_input == "" else user_input
    TITLE = title.strip()
    ALBUM = TITLE
    safe_filename = sanitize_filename(TITLE)
    final_path = os.path.join(FOLDER, f"{safe_filename}")
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
            f"title={TITLE}",
            "-metadata",
            f"album={ALBUM}",
        ],
        "outtmpl": final_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    PATH = f"{final_path}.{EXT}"
    file_size_bytes = os.path.getsize(PATH)
    file_size_mb = file_size_bytes / (1024 * 1024)
    desc = f"""File salvato come: {PATH}
    Dimensione: {file_size_mb:.2f} MB
    METADATA:
      Title: {TITLE}
      Album: {ALBUM}
      Artist: {artist}
      Date: {upload_date}
      Cover:  Embedded (from {thumbnail})
    """
    print(desc)
    return desc, PATH


if __name__ == "__main__":
    url = "https://music.youtube.com/watch?v=dKXgUs2icDI"
    get_single(url)
