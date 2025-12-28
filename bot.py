from telegram.ext import ApplicationBuilder, MessageHandler, filters
from handlers import handle_message
from config import BOT_TOKEN

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🦕 Dino standing by")
app.run_polling()