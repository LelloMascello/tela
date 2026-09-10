import os
import pymupdf  # Sostituito fitz (deprecato) con pymupdf per i file PDF
import docx  # python-docx per i file Word
import easyocr # OCR per le immagini
from app.core.database import get_db_connection
from app.services.search import index_note

# Inizializzazione lazy del reader OCR per non bloccare il caricamento iniziale di FastAPI
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        # Carica i modelli per italiano e inglese (scaricati al primo avvio)
        _ocr_reader = easyocr.Reader(['it', 'en'])
    return _ocr_reader

def extract_text(filepath: str, extension: str) -> str:
    """Estrae il testo in base all'estensione del file fornito."""
    text = ""
    try:
        if extension == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
        elif extension == 'docx':
            doc = docx.Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
            
        elif extension == 'pdf':
            # Utilizzo della nuova API pymupdf
            with pymupdf.open(filepath) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
                    
        elif extension in ['jpg', 'jpeg', 'png', 'webp']:
            reader = get_ocr_reader()
            # detail=0 restituisce solo una lista di stringhe senza le coordinate dei bounding box
            result = reader.readtext(filepath, detail=0)
            text = " ".join(result)
            
    except Exception as e:
        print(f"Errore durante l'estrazione da {filepath}: {e}")
        raise e
    
    return text.strip()

def process_note_background(note_id: str, filepath: str, extension: str):
    """Task eseguito in background da FastAPI per non bloccare l'upload."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Estrazione del testo
        extracted_text = extract_text(filepath, extension)
        
        # 2. Aggiornamento dello stato e salvataggio del testo in SQLite
        cursor.execute(
            "UPDATE notes SET status = ?, extracted_text = ? WHERE id = ?",
            ('completato', extracted_text, note_id)
        )
        conn.commit()
        print(f"Elaborazione completata per la nota {note_id}")
        
        # Ricaviamo il filename originale dal percorso fisico per indicizzarlo
        filename = os.path.basename(filepath)
        
        # Invia i dati a MeiliSearch per l'indicizzazione
        # Se search.py richiede i parametri in un ordine diverso, invertili qui sotto
        index_note(note_id, filename, extension, extracted_text)
        
    except Exception as e:
        print(f"Fallita elaborazione per {note_id}: {e}")
        # In caso di errore, aggiorniamo lo stato in modo che il frontend possa segnalarlo
        cursor.execute(
            "UPDATE notes SET status = ? WHERE id = ?",
            ('errore', note_id)
        )
        conn.commit()
    finally:
        conn.close()