import os

from dotenv import load_dotenv

load_dotenv()

DISCLAIMER = '[To set metadata automagically paste url of yt "Song" (not "Video")]'
ALLOWED_USERS: set[str] = (
    set(os.getenv("USERS_ALLOWED_TO_SAVE", "").split(","))
    if os.getenv("USERS_ALLOWED_TO_SAVE")
    else {"*"}
)
BOT_USERS: set[str] = (
    set(os.getenv("USERS_ALLOWED", "").split(","))
    if os.getenv("USERS_ALLOWED")
    else {"*"}
)

PLAYLIST_REGEX = r"https?://(www\.)?(youtube\.com|music\.youtube\.com)/playlist\?list=[a-zA-Z0-9_-]+"
SINGLE_REGEX = r"https?://(www\.)?(youtube\.com/watch\?v=|music\.youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+"


def allowed(user_id: int) -> bool:
    return "*" in BOT_USERS or str(user_id) in BOT_USERS


def authorized(user_id: int) -> bool:
    return "*" in ALLOWED_USERS or str(user_id) in ALLOWED_USERS


def get_folder(return_file: bool) -> str:
    if return_file:
        return os.getenv("TMP_FOLDER", "./tmp/")
    return os.getenv("SAVE_FOLDER", "./downloads/")


def get_ext() -> str:
    return os.getenv("EXT", "mp3")
