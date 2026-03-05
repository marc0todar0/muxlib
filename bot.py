import os
import re
import shutil
import traceback
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from single import get_single, get_single_info
from album import get_album, get_album_info

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


def allowed(user_id: int) -> bool:
    return "*" in BOT_USERS or str(user_id) in BOT_USERS


def authorized(user_id: int) -> bool:
    return "*" in ALLOWED_USERS or str(user_id) in ALLOWED_USERS


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.message is not None
    if not allowed(update.effective_user.id):
        return
    user = update.effective_user
    auth = authorized(user.id)
    default_action = (
        "Save Mp3 file on the server." if auth else "Send Mp3 file in the chat."
    )
    await update.message.reply_text(
        f"👤 Your Info:\n"
        f"User ID: {user.id}\n"
        f"Username: @{user.username}\n"
        f"Name: {user.first_name} {user.last_name or ''}\n"
        f"Allowed to save on server: {auth}\n"
        f"DEFAULT action on url pasted: {default_action}\n"
        f"{DISCLAIMER}"
    )


async def handle_album_url(
    update: Update, url: str, return_file: bool, folder: str
) -> None:
    assert update.message is not None
    try:
        info = get_album_info(url)
        action = "📥 Downloading" if return_file else "💾 Saving"
        await update.message.reply_text(
            f"{action} album: {info.title} by {info.artist} ({len(info.tracks)} tracks)..."
        )
        album_info, file_paths = get_album(
            url, FOLDER=folder, EXT=os.getenv("EXT", "mp3")
        )
        if return_file:
            for fp in file_paths:
                with open(fp, "rb") as audio:
                    await update.message.reply_audio(audio)
            album_folder = os.path.dirname(file_paths[0])
            shutil.rmtree(album_folder)
            await update.message.reply_text(
                f"✅ Sent album: {album_info.title} ({len(file_paths)} tracks)"
            )
        else:
            total_size = sum(
                os.path.getsize(fp) / (1024 * 1024) for fp in file_paths
            )
            date = album_info.date
            if date:
                date_obj = datetime.strptime(date, "%Y%m%d")
                date = date_obj.strftime("%d/%m/%Y")
            message = (
                f"✅ Album saved to server:\n\n"
                f"💿 Album: {album_info.title}\n"
                f"🎤 Artist: {album_info.artist}\n"
                f"📅 Date: {date}\n"
                f"🎵 Tracks: {len(file_paths)}\n"
                f"💾 Total size: {total_size:.2f} MB"
            )
            await update.message.reply_text(message)
    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def handle_url(
    update: Update, context: ContextTypes.DEFAULT_TYPE, return_file: bool | None = None
) -> None:
    assert update.effective_user is not None
    assert update.message is not None
    user_id = update.effective_user.id
    if not allowed(user_id):
        return
    if return_file is None:
        return_file = not authorized(user_id)
    message_text = update.message.text or ""
    print(f"handle_url received message_text: {message_text}")
    playlist_regex = r"https?://(www\.)?(youtube\.com|music\.youtube\.com)/playlist\?list=[a-zA-Z0-9_-]+"
    youtube_regex = r"https?://(www\.)?(youtube\.com/watch\?v=|music\.youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+"
    folder = os.getenv("SAVE_FOLDER", "./downloads/")
    if return_file:
        folder = os.getenv("TMP_FOLDER", "./tmp/")
    playlist_match = re.search(playlist_regex, message_text)
    if playlist_match:
        await handle_album_url(update, playlist_match.group(0), return_file, folder)
        return
    match = re.search(youtube_regex, message_text)
    if match:
        url = match.group(0)
        try:
            info = get_single_info(url=url)
            if return_file:
                await update.message.reply_text(
                    f"📥 Downloading {info.title} by {info.artist}..."
                )
            else:
                await update.message.reply_text(
                    f"💾 Saving {info.title} by {info.artist} to server..."
                )
            file_path = get_single(url, FOLDER=folder, EXT=os.getenv("EXT", "mp3"))
            if return_file:
                with open(file_path, "rb") as audio:
                    await update.message.reply_audio(audio)
                os.remove(file_path)
                await update.message.reply_text(f"✅ Sent: {info.title}")
            else:
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                date = info.date
                if info.date:
                    date_obj = datetime.strptime(info.date, "%Y%m%d")
                    date = date_obj.strftime("%d/%m/%Y")
                message = (
                    f"✅ Saved to server:\n\n"
                    f"🎵 Title: {info.title}\n"
                    f"🎤 Artist: {info.artist}\n"
                    f"💿 Album: {info.album}\n"
                    f"📅 Date: {date}\n"
                    f"📁 File: {os.path.basename(file_path)}\n"
                    f"💾 Size: {file_size:.2f} MB\n"
                    f"🖼️ Cover: {'✅ Embedded' if info.thumbnail else '❌ None'}"
                )
                await update.message.reply_text(message)
        except Exception as e:
            traceback.print_exc()
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    else:
        print("url non valido!", message_text)
        reply_text = (
            "❌ Formato URL non valido!\n\n"
            "Formati accettati:\n"
            "• https://www.youtube.com/watch?v=VIDEO_ID\n"
            "• https://music.youtube.com/watch?v=VIDEO_ID\n"
            "• https://youtu.be/VIDEO_ID\n"
            "• https://music.youtube.com/playlist?list=PLAYLIST_ID\n"
            f"{DISCLAIMER}"
        )
        await update.message.reply_text(reply_text)


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_url(update, context, return_file=True)


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.message is not None
    user_id = update.effective_user.id
    if not allowed(user_id):
        return
    if not authorized(user_id):
        await update.message.reply_text(
            "❌ You are not authorized to save files on the server!"
        )
        return
    await handle_url(update, context, return_file=False)


async def post_init(application: Application) -> None:  # type: ignore[type-arg]
    await application.bot.set_my_commands(
        [
            BotCommand("myid", "Get your user ID"),
            BotCommand("download", "📥 Download and send MP3 file"),
            BotCommand("save", "💾 Save MP3 to server (admin only)"),
        ]
    )


token = os.getenv("TGTOKEN")
assert token is not None, "TGTOKEN environment variable is required"
app = ApplicationBuilder().token(token).post_init(post_init).build()

app.add_handler(CommandHandler("download", download_command))
app.add_handler(CommandHandler("save", save_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
app.add_handler(CommandHandler("myid", myid))
print("Bot Starting...")
app.run_polling()
