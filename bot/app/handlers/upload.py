from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.client import BackendError, upload_file
from app.core.config import logger
from app.handlers.auth import restricted

# Tenuta in sync con allowed_extensions in backend/app/api/routes.py
ALLOWED_EXTENSIONS = {
    "txt", "pdf", "docx", "jpg", "jpeg", "png", "webp",
    "pptx", "xlsx", "mp3", "wav", "mp4", "avi",
}


def _confirmation_text(filename: str, data: dict) -> str:
    return (
        f"✅ Archiviato: *{filename}*\n"
        f"🆔 `{data.get('id', '?')}`\n"
        f"📌 Stato: {data.get('status', '?')}"
    )


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

    await status_msg.edit_text(_confirmation_text(filename, data), parse_mode="Markdown")


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

    await status_msg.edit_text(_confirmation_text(filename, data), parse_mode="Markdown")
