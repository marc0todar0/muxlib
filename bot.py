from dotenv import load_dotenv
import os
import re
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from single import get_single

load_dotenv()

DISCLAIMER = '\n[NB: Per avere i metadati corretti seleziona i link con la dicitura "Brano" e non "Video"]'


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("/hello command received")
    await update.message.reply_text(f"Hello {update.effective_user.first_name}")


async def handle_url(
    update: Update, context: ContextTypes.DEFAULT_TYPE, return_file: bool = False
) -> None:
    message_text = update.message.text
    print(f"handle_url received message_text: {message_text}")
    youtube_regex = r"https?://(www\.)?(youtube\.com/watch\?v=|music\.youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+"
    match = re.search(youtube_regex, message_text)
    if match:
        url = match.group(0)
        await update.message.reply_text("📥 Downloading...")
        try:
            desc, file_path = get_single(
                url, FOLDER=os.getenv("FOLDER"), EXT=os.getenv("EXT")
            )
            desc += DISCLAIMER
            if return_file:
                with open(file_path, "rb") as audio:
                    await update.message.reply_audio(audio)
                os.remove(file_path)
            else:
                await update.message.reply_text(desc)
            await update.message.reply_text("✅ Download completato!")
        except Exception as e:
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    else:
        print("url non valido!", message_text)
        reply_text = (
            "❌ Formato URL non valido!\n\n"
            "Formati accettati:\n"
            "• https://www.youtube.com/watch?v=VIDEO_ID\n"
            "• https://music.youtube.com/watch?v=VIDEO_ID\n"
            "• https://youtu.be/VIDEO_ID"
            f"{DISCLAIMER}"
        )
        await update.message.reply_text(reply_text)


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_url(update, context, return_file=True)


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_url(update, context, return_file=False)


async def post_init(application):
    """Imposta i comandi del bot dopo l'inizializzazione"""
    await application.bot.set_my_commands(
        [
            BotCommand("hello", "Saluta l'utente"),
            BotCommand("download", "Invia MP3 in chat - /download <url>"),
            BotCommand("save", "Salva MP3 sul server - /save <url>"),
        ]
    )


app = ApplicationBuilder().token(os.getenv("TGTOKEN")).post_init(post_init).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("download", download_command))  # Scarica e invia file
app.add_handler(CommandHandler("save", save_command))  # Scarica senza inviare
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_command))
# filters.TEXT & ~filters.COMMAND = "messaggi di testo che non sono comandi"
print("Bot Starting...")
app.run_polling()
