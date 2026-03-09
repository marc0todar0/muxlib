import os
import re
import shutil
import traceback

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from muxlib.config import (
    DISCLAIMER,
    PLAYLIST_REGEX,
    SINGLE_REGEX,
    allowed,
    authorized,
    get_ext,
    get_folder,
)
from muxlib.downloader import get_album, get_album_info, get_single, get_single_info
from muxlib.utils import format_date


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


async def handle_single_url(
    update: Update, url: str, return_file: bool, folder: str
) -> None:
    assert update.message is not None
    try:
        info = get_single_info(url=url)
        action = "📥 Downloading" if return_file else "💾 Saving"
        await update.message.reply_text(
            f"{action} {info.title} by {info.artist}..."
        )
        file_path = get_single(url, FOLDER=folder, EXT=get_ext())
        if return_file:
            with open(file_path, "rb") as audio:
                await update.message.reply_audio(audio)
            os.remove(file_path)
            await update.message.reply_text(f"✅ Sent: {info.title}")
        else:
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            message = (
                f"✅ Saved to server:\n\n"
                f"🎵 Title: {info.title}\n"
                f"🎤 Artist: {info.artist}\n"
                f"💿 Album: {info.album}\n"
                f"📅 Date: {format_date(info.date)}\n"
                f"📁 File: {os.path.basename(file_path)}\n"
                f"💾 Size: {file_size:.2f} MB\n"
                f"🖼️ Cover: {'✅ Embedded' if info.thumbnail else '❌ None'}"
            )
            await update.message.reply_text(message)
    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text(f"❌ Errore: {str(e)}")


async def handle_album_url(
    update: Update, url: str, return_file: bool, folder: str, force_album: bool | None = None
) -> None:
    assert update.message is not None
    try:
        info = get_album_info(url, force_album=force_album)
        action = "📥 Downloading" if return_file else "💾 Saving"
        label = "album" if info.is_album else "playlist"
        if info.is_album:
            await update.message.reply_text(
                f"{action} {label}: {info.title} by {info.artist} ({len(info.tracks)} tracks)..."
            )
        else:
            await update.message.reply_text(
                f"{action} {label}: {info.title} ({len(info.tracks)} tracks)..."
            )
        album_info, file_paths = get_album(url, FOLDER=folder, EXT=get_ext(), force_album=force_album)
        if return_file:
            for fp in file_paths:
                with open(fp, "rb") as audio:
                    await update.message.reply_audio(audio)
            album_folder = os.path.dirname(file_paths[0])
            shutil.rmtree(album_folder)
            await update.message.reply_text(
                f"✅ Sent {label}: {album_info.title} ({len(file_paths)} tracks)"
            )
        else:
            total_size = sum(
                os.path.getsize(fp) / (1024 * 1024) for fp in file_paths
            )
            if album_info.is_album:
                message = (
                    f"✅ Album saved to server:\n\n"
                    f"💿 Album: {album_info.title}\n"
                    f"🎤 Artist: {album_info.artist}\n"
                    f"📅 Date: {format_date(album_info.date)}\n"
                    f"🎵 Tracks: {len(file_paths)}\n"
                    f"💾 Total size: {total_size:.2f} MB"
                )
            else:
                message = (
                    f"✅ Playlist saved to server:\n\n"
                    f"📋 Playlist: {album_info.title}\n"
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
    folder = get_folder(return_file)

    force_album: bool | None = None
    if "--album" in message_text:
        force_album = True
    elif "--playlist" in message_text:
        force_album = False

    playlist_match = re.search(PLAYLIST_REGEX, message_text)
    if playlist_match:
        await handle_album_url(update, playlist_match.group(0), return_file, folder, force_album=force_album)
        return

    single_match = re.search(SINGLE_REGEX, message_text)
    if single_match:
        await handle_single_url(update, single_match.group(0), return_file, folder)
        return

    await update.message.reply_text(
        "❌ Formato URL non valido!\n\n"
        "Formati accettati:\n"
        "• https://www.youtube.com/watch?v=VIDEO_ID\n"
        "• https://music.youtube.com/watch?v=VIDEO_ID\n"
        "• https://youtu.be/VIDEO_ID\n"
        "• https://music.youtube.com/playlist?list=PLAYLIST_ID\n"
        f"{DISCLAIMER}"
    )


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


def create_app() -> Application:  # type: ignore[type-arg]
    token = os.getenv("TGTOKEN")
    assert token is not None, "TGTOKEN environment variable is required"
    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("download", download_command))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CommandHandler("myid", myid))

    return app
