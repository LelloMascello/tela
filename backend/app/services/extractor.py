import os
import pymupdf
import docx
import easyocr
from pptx import Presentation
import openpyxl
from faster_whisper import WhisperModel
from app.core.database import get_db_connection
from app.services.search import index_note

_ocr_reader = None
_whisper_model = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['it', 'en'])
    return _ocr_reader

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        # device="cpu" o "cuda" a seconda dell'hardware. compute_type="int8" riduce l'impatto in RAM
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model

def extract_text(filepath: str, extension: str) -> str:
    text = ""
    try:
        if extension == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
        elif extension == 'docx':
            doc = docx.Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
            
        elif extension == 'pdf':
            with pymupdf.open(filepath) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
                    
        elif extension in ['jpg', 'jpeg', 'png', 'webp']:
            reader = get_ocr_reader()
            result = reader.readtext(filepath, detail=0)
            text = " ".join(result)

        elif extension == 'pptx':
            prs = Presentation(filepath)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
                        
        elif extension == 'xlsx':
            wb = openpyxl.load_workbook(filepath, data_only=True)
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = " ".join([str(cell) for cell in row if cell is not None])
                    if row_text.strip():
                        text += row_text + "\n"
                        
        elif extension in ['mp3', 'wav', 'mp4', 'avi']:
            model = get_whisper_model()
            # faster-whisper accetta direttamente sia file audio che video
            segments, info = model.transcribe(filepath, beam_size=5)
            # segments è un generatore, iteriamo per concatenare il testo
            text = " ".join([segment.text for segment in segments])
                
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