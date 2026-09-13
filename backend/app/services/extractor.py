import atexit
from concurrent.futures import ThreadPoolExecutor

import docx
import easyocr
import openpyxl
import pymupdf
from faster_whisper import WhisperModel
from pptx import Presentation

from app.core.database import get_db_connection, update_note_text

_ocr_reader = None
_whisper_model = None


def get_ocr_reader():
    # Lazy singleton: carica EasyOCR una sola volta e lo riusa
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['it', 'en'])
    return _ocr_reader


def get_whisper_model():
    # Lazy singleton: carica Faster-Whisper una sola volta e lo riusa
    global _whisper_model
    if _whisper_model is None:
        # compute_type="int8" riduce l'uso di RAM su CPU
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model


def extract_text(filepath: str, extension: str) -> str:
    # Estrae il testo in base al formato del file
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
            # OCR sull'immagine
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
            # Trascrizione audio/video
            model = get_whisper_model()
            segments, _info = model.transcribe(filepath, beam_size=5)
            text = " ".join([segment.text for segment in segments])

    except Exception as e:
        print(f"Errore durante l'estrazione da {filepath}: {e}")
        raise e

    return text.strip()


# Coda a singolo worker: evita estrazioni in parallelo e il rischio di OOM
# su hardware a basso consumo. I job vengono eseguiti uno alla volta, in
# ordine FIFO.
_extraction_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="tela-extractor-worker",
)

# Attende il job in corso prima di terminare il processo
atexit.register(_extraction_executor.shutdown, wait=True)


def process_note_background(note_id: str, filepath: str, extension: str):
    # Punto d'ingresso invariato: accoda il job e ritorna subito
    _extraction_executor.submit(_process_note_job, note_id, filepath, extension)


def _process_note_job(note_id: str, filepath: str, extension: str):
    # Job eseguito dal singolo worker della coda
    try:
        extracted_text = extract_text(filepath, extension)
        # Aggiorna testo, titolo automatico, status e indice MeiliSearch
        update_note_text(note_id, extracted_text, status='completato')
        print(f"Elaborazione completata per la nota {note_id}")

    except Exception as e:
        print(f"Fallita elaborazione per {note_id}: {e}")
        try:
            # In caso di errore aggiorna solo lo status
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE notes SET status = ? WHERE id = ?",
                ('errore', note_id)
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            # Il worker non si blocca: passa comunque al job successivo
            print(f"Errore anche nell'aggiornare lo status di {note_id}: {db_err}")