import os
import sqlite3
import meilisearch
from app.core.config import DB_PATH, MEILI_HOST, MEILI_API_KEY, UPLOAD_DIR

def get_db_connection():
    # check_same_thread=False è necessario in FastAPI per condividere la connessione tra le richieste
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # row_factory permette di accedere ai risultati come dizionari (es. row['id'])
    conn.row_factory = sqlite3.Row
    return conn

def get_meili_client():
    return meilisearch.Client(MEILI_HOST, MEILI_API_KEY)

def init_dbs():
    """Inizializza le tabelle SQLite e gli indici di MeiliSearch al boot."""
    # 1. Inizializzazione SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            extension TEXT NOT NULL,
            status TEXT NOT NULL,
            extracted_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database SQLite inizializzato.")

    # 2. Inizializzazione MeiliSearch
    try:
        client = get_meili_client()
        # Crea l'indice se non esiste (la primary key sarà l'ID del database)
        client.create_index('notes', {'primaryKey': 'id'})
        
        # Opzionale ma consigliato: configura quali campi sono ricercabili
        client.index('notes').update_searchable_attributes(['extracted_text', 'filename', 'extension'])
        print("MeiliSearch connesso e indice 'notes' verificato.")
    except Exception as e:
        print(f"Avviso: Connessione a MeiliSearch non riuscita al momento del setup. Errore: {e}")


def delete_note(note_id: str) -> bool:
    """Elimina definitivamente una nota: rimuove la riga da SQLite, il file
    originale su disco e il documento corrispondente dall'indice MeiliSearch.

    Ritorna True se la nota esisteva ed è stata eliminata, False se non è
    stata trovata (in questo caso non viene toccato nulla).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    if not note:
        conn.close()
        return False

    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

    # Rimuove il file originale dal disco, se presente. Un file mancante non
    # deve bloccare l'eliminazione del record.
    filepath = os.path.join(UPLOAD_DIR, note["filename"])
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError as e:
        print(f"Avviso: impossibile rimuovere il file {filepath}. Errore: {e}")

    # Rimuove il documento dall'indice di MeiliSearch. Se MeiliSearch non è
    # raggiungibile, la nota resta comunque eliminata dal database.
    try:
        get_meili_client().index('notes').delete_document(note_id)
    except Exception as e:
        print(f"Avviso: impossibile rimuovere la nota {note_id} da MeiliSearch. Errore: {e}")

    return True