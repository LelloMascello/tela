import logging
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tela_bot")

# --- Obbligatorie ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN non impostato. Aggiungilo al file .env "
        "(vedi bot/README.md)."
    )

# --- Opzionali (con default sensati) ---

# URL interno del backend FastAPI (nome del container Docker, non serve esporre porte)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")

# URL pubblico/VPN del frontend, usato dal comando /sito
WEBSITE_URL = os.environ.get("WEBSITE_URL", "")

# Lista di user_id Telegram autorizzati a usare il bot, separati da virgola.
# Se lasciata vuota il bot risponde a chiunque: SCONSIGLIATO per un archivio personale.
_raw_allowed = os.environ.get("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = {
    int(uid.strip()) for uid in _raw_allowed.split(",") if uid.strip().isdigit()
}
if not ALLOWED_USER_IDS:
    logger.warning(
        "ALLOWED_USER_IDS non impostato: il bot risponderà a QUALSIASI utente Telegram. "
        "Imposta questa variabile nel file .env per limitare l'accesso al tuo archivio personale."
    )

# Numero massimo di risultati mostrati per una ricerca
MAX_SEARCH_RESULTS = int(os.environ.get("MAX_SEARCH_RESULTS", "8"))
