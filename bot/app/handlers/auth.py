from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import ALLOWED_USER_IDS, logger


def restricted(handler):
    """
    Decorator che blocca l'esecuzione dell'handler se l'utente non è
    presente in ALLOWED_USER_IDS. Se ALLOWED_USER_IDS è vuoto, non blocca nessuno
    (vedi warning in config.py).
    """

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user

        if ALLOWED_USER_IDS and (user is None or user.id not in ALLOWED_USER_IDS):
            logger.warning(
                "Accesso negato per user_id=%s username=%s",
                user.id if user else None,
                user.username if user else None,
            )
            if update.callback_query:
                await update.callback_query.answer("⛔ Non autorizzato", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text("⛔ Non sei autorizzato a usare questo bot.")
            return

        return await handler(update, context, *args, **kwargs)

    return wrapper
