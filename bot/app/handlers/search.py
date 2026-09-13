from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.client import BackendError, download_note_file, export_notes_zip, search_notes
from app.core.config import MAX_SEARCH_RESULTS, logger
from app.handlers.auth import restricted

# Prefisso del callback_data usato dai bottoni di navigazione tra pagine di risultati.
PAGE_PREFIX = "page:"

# Callback_data del bottone di esportazione in blocco (nessun parametro extra
# necessario: legge query e id direttamente da context.user_data["last_search"]).
EXPORT_CALLBACK_DATA = "export_zip"


def _build_caption(query: str, total: int, offset: int) -> str:
    """Costruisce la didascalia mostrando l'intervallo di risultati visualizzato."""
    caption = f"🔍 {total} risultati per «{query}»"
    if total > MAX_SEARCH_RESULTS:
        shown_end = min(offset + MAX_SEARCH_RESULTS, total)
        caption += f" — {offset + 1}-{shown_end}"
    return caption


def _build_markup(hits: list, offset: int) -> InlineKeyboardMarkup:
    """Costruisce i bottoni per la pagina corrente, con navigazione avanti/indietro."""
    page = hits[offset:offset + MAX_SEARCH_RESULTS]

    buttons = [
        [InlineKeyboardButton(
            f"📄 {hit.get('title') or hit.get('filename', hit.get('id'))}",
            callback_data=f"dl:{hit['id']}"
        )]
        for hit in page
    ]

    nav_row = []
    if offset > 0:
        prev_offset = max(0, offset - MAX_SEARCH_RESULTS)
        nav_row.append(InlineKeyboardButton(
            "⬅️ Precedenti", callback_data=f"{PAGE_PREFIX}{prev_offset}"
        ))

    next_offset = offset + MAX_SEARCH_RESULTS
    remaining = len(hits) - next_offset
    if remaining > 0:
        nav_row.append(InlineKeyboardButton(
            f"➡️ Carica altri ({remaining})", callback_data=f"{PAGE_PREFIX}{next_offset}"
        ))

    if nav_row:
        buttons.append(nav_row)

    # Esportazione in blocco: scarica in un unico .zip le trascrizioni di
    # *tutti* i risultati della ricerca corrente, non solo quelli della pagina
    # mostrata. Presente su ogni pagina, non solo sulla prima.
    buttons.append([InlineKeyboardButton(
        f"📦 Esporta tutto in .zip ({len(hits)})", callback_data=EXPORT_CALLBACK_DATA
    )])

    return InlineKeyboardMarkup(buttons)


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

    # Salva la ricerca corrente per permettere la navigazione avanti/indietro.
    # NB: viene mantenuta solo l'ultima ricerca per utente: se l'utente lancia una
    # nuova ricerca, i bottoni di navigazione di una ricerca precedente non saranno
    # più validi (l'utente riceverà un messaggio che lo invita a ripetere /cerca).
    context.user_data["last_search"] = {"query": query, "hits": hits}

    caption = _build_caption(query, len(hits), 0)
    markup = _build_markup(hits, 0)

    await update.message.reply_text(caption, reply_markup=markup)


@restricted
async def paginate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()

    try:
        offset = int(callback.data[len(PAGE_PREFIX):])
    except (ValueError, IndexError):
        await callback.message.reply_text("❌ Richiesta non valida.")
        return

    state = context.user_data.get("last_search")
    if not state:
        await callback.message.reply_text(
            "⏳ Sessione di ricerca scaduta. Ripeti la ricerca con /cerca."
        )
        return

    hits = state["hits"]
    query = state["query"]

    if not 0 <= offset < len(hits):
        # Offset fuori range (es. doppio click): non c'è nulla da aggiornare.
        return

    caption = _build_caption(query, len(hits), offset)
    markup = _build_markup(hits, offset)

    await callback.edit_message_text(caption, reply_markup=markup)


@restricted
async def export_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera e invia lo .zip con le trascrizioni di tutti i risultati
    dell'ultima ricerca salvata per questo utente."""
    callback = update.callback_query
    await callback.answer()

    state = context.user_data.get("last_search")
    if not state:
        await callback.message.reply_text(
            "⏳ Sessione di ricerca scaduta. Ripeti la ricerca con /cerca."
        )
        return

    hits = state["hits"]
    query = state["query"]
    note_ids = [hit["id"] for hit in hits]

    # Mostra "sta caricando un file" mentre il backend prepara lo zip,
    # che su ricerche con molti risultati può richiedere qualche secondo.
    await context.bot.send_chat_action(chat_id=callback.message.chat_id, action="upload_document")

    try:
        content, filename = await export_notes_zip(note_ids)
    except BackendError as e:
        logger.error("Errore esportazione zip: %s", e)
        await callback.message.reply_text("❌ Esportazione fallita: errore del backend.")
        return

    await callback.message.reply_document(
        document=content,
        filename=filename,
        caption=f"📦 {len(note_ids)} trascrizioni per «{query}»"
    )


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