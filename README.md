# muxlib

A personal music library manager. Downloads YouTube audio as MP3, manages metadata, and (soon) tracks your library in a database.

NB: yt-dlp must be kept updated — YouTube changes frequently.

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
- `https://music.youtube.com/playlist?list=PLAYLIST_ID`

### Album vs Playlist Detection

When a playlist URL is sent, the bot auto-detects whether it's an **album** or a **user-curated playlist**:

- **Album**: all tracks share the same `album` metadata field, or the playlist title starts with "Album - ". Tracks get numbered (`01`, `02`, ...) and share the album name in ID3 tags.
- **Playlist**: tracks come from different albums/artists. Each track keeps its own original metadata (artist, album). No track numbering in ID3 tags.

You can override detection by adding a flag to the message:

| Flag | Effect |
|------|--------|
| `--album` | Force album mode (shared album name, track numbers) |
| `--playlist` | Force playlist mode (each track keeps its own metadata) |

**Telegram example:** `--playlist https://music.youtube.com/playlist?list=PLAYLIST_ID`

**CLI example:** `python cli.py --playlist --info-only <playlist_url>`


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

## RUN

```bash
```
python -m muxlib
```
```

## Testing

Requires `ffmpeg` installed and network access (tests hit real YouTube).

```bash
python -m pytest -v -s
```

### Notes
- Files are automatically tagged with ID3 metadata (title, artist, album, cover art)

### Dependencies:
- https://github.com/yt-dlp/yt-dlp
- https://python-telegram-bot.org/

---

## Roadmap

### Done
- [x] Single track download (YouTube / YouTube Music)
- [x] Album / playlist download with auto-detection
- [x] ID3 metadata tagging (title, artist, album, cover art, track number)
- [x] Telegram bot with `/download`, `/save`, `/myid` commands
- [x] CLI tool for local downloads
- [x] `--album` / `--playlist` override flags
- [x] Docker deployment

### Next
- [ ] **Library database** — SQLite/Postgres DB that syncs with the download folder, tracking every song and album
- [ ] **Metadata management** — View and edit ID3 tags from Telegram or CLI
- [ ] **Duplicate detection** — Detect and handle duplicate tracks across albums/playlists
- [ ] **Delete songs/albums** — Remove tracks from folder + DB via bot command or CLI
- [ ] **Library search** — Search your library by title, artist, album from Telegram
- [ ] **Sync engine** — Watch folder for external changes and keep DB in sync
- [ ] **Stats & history** — Download history, library size, most downloaded artists

