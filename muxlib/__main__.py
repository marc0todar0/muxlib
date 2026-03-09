from muxlib.handlers import create_app

app = create_app()
print("Bot Starting...")
app.run_polling()
