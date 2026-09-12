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

def generate_title(text: str | None, fallback: str) -> str:
    """Genera automaticamente il titolo di una nota a partire dal testo
    estratto: i primi 30 caratteri del testo, con puntini di sospensione
    aggiunti in fondo se il testo è più lungo. Se non c'è ancora testo
    disponibile (es. estrazione in corso o fallita), usa 'fallback'
    (tipicamente il filename) così il titolo non resta mai vuoto.
    """
    if not text:
        return fallback

    # Normalizza spazi/newline multipli così il titolo resta su una riga
    cleaned = " ".join(text.split())
    if not cleaned:
        return fallback

    if len(cleaned) <= 30:
        return cleaned

    return cleaned[:30].rstrip() + "..."

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
            title TEXT,
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
        client.index('notes').update_searchable_attributes(['title', 'extracted_text', 'filename', 'extension'])
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


def update_note_text(note_id: str, extracted_text: str, status: str | None = None) -> dict | None:
    """Aggiorna il testo estratto di una nota e ricalcola automaticamente il
    titolo (primi 30 caratteri del testo + puntini di sospensione),
    sincronizzando anche l'indice MeiliSearch.

    Usata in due punti:
    - dal worker di estrazione (services/extractor.py) quando l'OCR/parsing
      termina, passando lo status finale (es. 'completato' o 'errore');
    - dall'endpoint PATCH /api/notes/{id} quando l'utente corregge a mano la
      trascrizione dal DetailModal (qui lo status non viene toccato).

    Ritorna la nota aggiornata come dizionario, o None se l'id non esiste.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return None

    title = generate_title(extracted_text, fallback=existing["filename"])
    new_status = status if status is not None else existing["status"]

    cursor.execute(
        "UPDATE notes SET extracted_text = ?, title = ?, status = ? WHERE id = ?",
        (extracted_text, title, new_status, note_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    updated_note = dict(cursor.fetchone())
    conn.close()

    # Aggiorna anche MeiliSearch (update_documents fa un merge sui campi
    # esistenti). Includiamo filename/extension oltre a quelli cambiati così
    # questa funzione basta da sola a indicizzare la nota anche la prima
    # volta (fine estrazione), senza bisogno di una chiamata add_documents
    # separata altrove. Se MeiliSearch non è raggiungibile, la nota resta
    # comunque aggiornata su SQLite.
    try:
        get_meili_client().index('notes').update_documents([{
            'id': note_id,
            'filename': existing["filename"],
            'extension': existing["extension"],
            'extracted_text': extracted_text,
            'title': title,
            'status': new_status,
        }])
    except Exception as e:
        print(f"Avviso: impossibile aggiornare la nota {note_id} su MeiliSearch. Errore: {e}")

    return updated_note