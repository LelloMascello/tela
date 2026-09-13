import os

# Definizione delle directory di base
# Utilizziamo variabili d'ambiente con valori di default per facilitare il deploy con Docker
DATA_DIR = os.getenv("TELA_DATA_DIR", "./data")

# Percorsi specifici per i volumi
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "database", "tela.db")

# Configurazione MeiliSearch
MEILI_HOST = os.getenv("MEILI_HOST", "http://meilisearch:7700")
MEILI_API_KEY = os.getenv("MEILI_API_KEY", "chiave_segreta_tela_123")

# Numero massimo di note esportabili in un'unica richiesta di esportazione in
# blocco (POST /api/notes/export): protegge il server da uno zip abnorme se
# venisse passata una lista di id enorme.
EXPORT_MAX_IDS = int(os.getenv("TELA_EXPORT_MAX_IDS", "500"))

# Creazione automatica delle cartelle necessarie all'avvio
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)