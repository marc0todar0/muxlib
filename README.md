# Bot - yt-dlp downloader wrapper
NB: Its important to keep yt-dlp always updated!

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/hello` | Greet the user | `/hello` |
| `/download <url>` | Download a YouTube video and send the MP3 file via Telegram | `/download https://youtube.com/watch?v=VIDEO_ID` |
| `/save <url>` | Download a YouTube video and save the MP3 file on the server | `/save https://music.youtube.com/watch?v=VIDEO_ID` |

### Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://music.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`

### Notes

- You can also send a YouTube URL without any command (default behavior: saves on server without sending the file)
- Files are automatically tagged with ID3 metadata (title, artist, album, cover art)

### Refs:
- https://github.com/yt-dlp/yt-dlp
- https://python-telegram-bot.org/
