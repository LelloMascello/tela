from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.core.config import TELEGRAM_BOT_TOKEN, logger
from app.handlers.search import cerca, download_callback
from app.handlers.site import sito
from app.handlers.start import help_command, start
from app.handlers.upload import handle_document, handle_photo


def build_application() -> Application:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sito", sito))
    application.add_handler(CommandHandler("cerca", cerca))

    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.add_handler(CallbackQueryHandler(download_callback, pattern=r"^dl:"))

    return application


def main():
    logger.info("Avvio TELA bot (long polling)...")
    application = build_application()
    # allowed_updates limita ciò che Telegram invia al bot: risparmia banda/CPU sul Pi
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
