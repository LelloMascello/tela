from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import WEBSITE_URL
from app.handlers.auth import restricted


@restricted
async def sito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WEBSITE_URL:
        await update.message.reply_text(
            "⚠️ L'URL del sito non è configurato (variabile WEBSITE_URL nel file .env)."
        )
        return
    await update.message.reply_text(f"🌐 Apri TELA: {WEBSITE_URL}")
