import asyncio

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.client import BackendError, upload_file, get_note_details
from app.core.config import logger
from app.handlers.auth import restricted

# Tenuta in sync con allowed_extensions in backend/app/api/routes.py
ALLOWED_EXTENSIONS = {
    "txt", "pdf", "docx", "jpg", "jpeg", "png", "webp",
    "pptx", "xlsx", "mp3", "wav", "mp4", "avi",
}

# Quanto aspettare (e con che frequenza controllare) che l'estrazione in
# background finisca prima di mostrare il titolo automatico. L'OCR e la
# trascrizione audio/video (Whisper) possono richiedere più tempo dei
# formati testuali, da qui un timeout generoso.
TITLE_POLL_INTERVAL_SECONDS = 5
TITLE_POLL_TIMEOUT_SECONDS = 600


def _confirmation_text(filename: str, data: dict) -> str:
    return (
        f"✅ Archiviato: *{filename}*\n"
        f"🆔 `{data.get('id', '?')}`\n"
        f"📌 Stato: {data.get('status', '?')}"
    )


def _title_ready_text(note: dict) -> str:
    if note.get("status") == "errore":
        return f"❌ Estrazione fallita per *{note.get('filename', '?')}*. Il file resta archiviato, ma senza testo/titolo automatico."
    title = note.get("title") or note.get("filename", "?")
    return f"📌 Titolo aggiornato: *{title}*"


async def _watch_for_title(status_msg, note_id: str, base_text: str):
    """L'estrazione testo gira in background sul backend dopo l'upload: qui
    la aspettiamo con un breve polling e, appena lo status non è più
    'in_elaborazione' (titolo automatico pronto, oppure estrazione fallita),
    aggiorniamo il messaggio di conferma al posto del filename randomico."""
    elapsed = 0
    while elapsed < TITLE_POLL_TIMEOUT_SECONDS:
        await asyncio.sleep(TITLE_POLL_INTERVAL_SECONDS)
        elapsed += TITLE_POLL_INTERVAL_SECONDS

        try:
            note = await get_note_details(note_id)
        except BackendError as e:
            logger.warning("Polling titolo fallito per %s: %s", note_id, e)
            return

        if note.get("status") != "in_elaborazione":
            try:
                await status_msg.edit_text(_title_ready_text(note), parse_mode="Markdown")
            except BadRequest:
                pass  # l'utente ha già cancellato/modificato il messaggio
            return

    # Timeout: l'estrazione sta impiegando più del previsto (es. video lunghi).
    try:
        await status_msg.edit_text(
            f"{base_text}\n\n⏳ L'estrazione sta impiegando più del previsto, "
            "riprova a cercare il file tra un po'.",
            parse_mode="Markdown",
        )
    except BadRequest:
        pass


@restricted
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    filename = doc.file_name or "file_senza_nome"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        await update.message.reply_text(f"⚠️ Formato \".{extension}\" non supportato da TELA.")
        return

    status_msg = await update.message.reply_text("⏳ Caricamento in corso...")

    try:
        tg_file = await doc.get_file()
    except BadRequest as e:
        if "too big" in str(e).lower():
            await status_msg.edit_text(
                "⚠️ File troppo grande: l'API Bot standard di Telegram consente il download "
                "di file inviati al bot fino a 20MB. Per file più grandi serve un Bot API "
                "server locale (vedi bot/README.md)."
            )
            return
        raise

    try:
        content = await tg_file.download_as_bytearray()
        data = await upload_file(filename, bytes(content), doc.mime_type)
    except BackendError as e:
        logger.error("Errore upload: %s", e)
        await status_msg.edit_text("❌ Caricamento fallito: il backend ha risposto con un errore.")
        return
    except Exception:
        logger.exception("Errore imprevisto durante l'upload")
        await status_msg.edit_text("❌ Errore imprevisto durante il caricamento.")
        return

    confirmation_text = _confirmation_text(filename, data)
    await status_msg.edit_text(confirmation_text, parse_mode="Markdown")
    context.application.create_task(_watch_for_title(status_msg, data.get("id"), confirmation_text))


@restricted
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Prende la risoluzione più alta disponibile tra quelle generate da Telegram
    photo = update.message.photo[-1]

    status_msg = await update.message.reply_text(
        "⏳ Caricamento in corso...\n"
        "ℹ️ Suggerimento: per una qualità OCR migliore, invia le immagini come *file* "
        "(📎 → File) invece che come foto.",
        parse_mode="Markdown",
    )

    filename = f"{photo.file_unique_id}.jpg"

    try:
        tg_file = await photo.get_file()
        content = await tg_file.download_as_bytearray()
        data = await upload_file(filename, bytes(content), "image/jpeg")
    except BackendError as e:
        logger.error("Errore upload foto: %s", e)
        await status_msg.edit_text("❌ Caricamento fallito: il backend ha risposto con un errore.")
        return
    except Exception:
        logger.exception("Errore imprevisto durante l'upload della foto")
        await status_msg.edit_text("❌ Errore imprevisto durante il caricamento.")
        return

    confirmation_text = _confirmation_text(filename, data)
    await status_msg.edit_text(confirmation_text, parse_mode="Markdown")
    context.application.create_task(_watch_for_title(status_msg, data.get("id"), confirmation_text))