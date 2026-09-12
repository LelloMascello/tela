from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.client import BackendError, download_note_file, search_notes
from app.core.config import MAX_SEARCH_RESULTS, logger
from app.handlers.auth import restricted


@restricted
async def cerca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /cerca <testo da cercare>")
        return

    query = " ".join(context.args)

    try:
        result = await search_notes(query)
    except BackendError as e:
        logger.error("Errore ricerca: %s", e)
        await update.message.reply_text("❌ Ricerca fallita: il backend ha risposto con un errore.")
        return

    hits = result.get("results", [])
    if not hits:
        await update.message.reply_text(f"Nessun risultato per «{query}».")
        return

    shown = hits[:MAX_SEARCH_RESULTS]
    buttons = [
        [InlineKeyboardButton(
            f"📄 {hit.get('title') or hit.get('filename', hit.get('id'))}",
            callback_data=f"dl:{hit['id']}"
        )]
        for hit in shown
    ]

    caption = f"🔍 {len(hits)} risultati per «{query}»"
    if len(hits) > MAX_SEARCH_RESULTS:
        caption += f" — mostro i primi {MAX_SEARCH_RESULTS}"

    await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(buttons))


@restricted
async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    note_id = query.data.split(":", 1)[1]

    try:
        content, filename = await download_note_file(note_id)
    except BackendError as e:
        logger.error("Errore download: %s", e)
        await query.message.reply_text("❌ Download fallito: file non trovato o errore del backend.")
        return

    await query.message.reply_document(document=content, filename=filename)