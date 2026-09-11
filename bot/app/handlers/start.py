from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.auth import restricted

HELP_TEXT = (
    "📚 *TELA Bot*\n\n"
    "Puoi:\n"
    "• Inviarmi un *file* (PDF, DOCX, TXT, PPTX, XLSX, immagine, audio, video) per archiviarlo\n"
    "  ℹ️ Invia le scansioni di appunti come *file* (📎 → File), non come foto: "
    "Telegram comprime le foto e peggiora la qualità dell'OCR.\n\n"
    "• `/cerca <testo>` — cerca nei documenti archiviati\n"
    "• `/sito` — apri l'interfaccia web di TELA\n"
    "• `/help` — mostra questo messaggio"
)


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
