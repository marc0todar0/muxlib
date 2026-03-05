# Bot - yt-dlp downloader wrapper
NB: Its important to keep yt-dlp always updated!

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/myid` | Get user informations and authorizations on the server. | `/myid` |
| `/download <url>` | Send the MP3 file via Telegram | `/download https://youtube.com/watch?v=VIDEO_ID` |
| `/save <url>` | Save the MP3 file on the server | `/save https://music.youtube.com/watch?v=VIDEO_ID` |
| `<url>` | Send/Save Mp3 from video url based on the default action (Save if user.id is in ALLOWED_USER, send otherwidse) | `https://music.youtube.com/watch?v=VIDEO_ID` |

### Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://music.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`


## ENVIRONMENT
- TGTOKEN="" # Your Personal Telegram Bot Token
- SAVE_FOLDER="./downloads/" #path where the /save command store the mp3 files e.g. "/mnt/storage/ROOT/MUSIC/"
- TMP_FOLDER="./tmp/"        # path where the /download command store and delete the mp3 to send it as a message response
- USERS_ALLOWED_TO_SAVE="*"  # list of users allowed to save mp3 on the server id1,id2,.. or "*"
- USERS_ALLOWED="*"          # list of users allowed to use the bot id1,id2,.. or "*" for everyone
- EXT="mp3"

## Docker Deploy

```bash
docker compose up --build -d
```

## Development Setup

```bash
pip install -r requirements-dev.txt
cp pre-commit .git/hooks/pre-commit
```

This installs dev tools (ruff, pyright, pytest) and enables the pre-commit hook that runs linting before each commit.

## Testing

Requires `ffmpeg` installed and network access (tests hit real YouTube).

```bash
python -m pytest -v
```

### Notes
- Files are automatically tagged with ID3 metadata (title, artist, album, cover art)

### Dependencies:
- https://github.com/yt-dlp/yt-dlp
- https://python-telegram-bot.org/
