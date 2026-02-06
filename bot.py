from dotenv import load_dotenv
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from single import get_single
load_dotenv()

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("/hello command received")
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    print(f"handle_url received message_text: {message_text}")
    if "youtube.com" in message_text:
        await update.message.reply_text("Downloading...")
        try:
            url = message_text.strip()
            get_single(url, FOLDER=os.getenv("FOLDER"), EXT=os.getenv("EXT"))
            await update.message.reply_text("✅ Download completato!")
        except Exception as e:
            await update.message.reply_text(f"❌ Errore: {str(e)}")
    else:
        print("url non valido!")
        await update.message.reply_text("url non valido!")

app = ApplicationBuilder().token(os.getenv("TGTOKEN")).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
print("Bot Starting...")
app.run_polling()
