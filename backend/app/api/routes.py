import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Importazioni attivate dai moduli core appena creati
from app.core.config import UPLOAD_DIR
from app.core.database import get_db_connection, delete_note, update_note_text

# Da decommentare quando scriveremo services/extractor.py e services/search.py
from app.services.extractor import process_note_background
from app.services.search import query_notes

router = APIRouter(prefix="/api", tags=["Notes"])


class UpdateTranscriptionPayload(BaseModel):
    extracted_text: str

@router.post("/upload")
async def upload_note(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1].lower()
    allowed_extensions = [
        'txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'webp',
        'pptx', 'xlsx', 'mp3', 'wav', 'mp4', 'avi'
    ]
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Formato non supportato")

    note_id = str(uuid.uuid4())
    safe_filename = f"{note_id}.{file_extension}"
    
    # 1. Utilizzare UPLOAD_DIR per comporre il percorso
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    
    # 2. Salvare fisicamente il file con shutil
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Connettersi a SQLite e fare l'INSERT
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (id, filename, extension, status) VALUES (?, ?, ?, ?)",
        (note_id, safe_filename, file_extension, 'in_elaborazione')
    )
    conn.commit()
    conn.close()
    
    # 4. Aggiungere il task in background (commentato finché non implementiamo extractor)
    background_tasks.add_task(process_note_background, note_id, filepath, file_extension)

    return {
        "id": note_id,
        "status": "in_elaborazione",
        "message": f"File {file_extension} salvato con successo. Estrazione in coda."
    }

@router.get("/notes")
def list_notes(limit: int = 50, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Recuperiamo gli appunti più recenti escludendo il testo estratto per alleggerire la risposta.
    # COALESCE(title, filename): finché l'estrazione non è completata (e il
    # titolo automatico non è ancora stato calcolato) mostriamo il filename
    # come placeholder, invece di un titolo nullo.
    cursor.execute(
        "SELECT id, filename, extension, status, COALESCE(title, filename) AS title, created_at FROM notes ORDER BY created_at DESC LIMIT ? OFFSET ?", 
        (limit, offset)
    )
    notes = cursor.fetchall()
    conn.close()
    
    # Ritorniamo i dati come array di dizionari
    return {"items": [dict(note) for note in notes]}

@router.get("/notes/{note_id}")
def get_note_details(note_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, extension, status, extracted_text, COALESCE(title, filename) AS title, created_at FROM notes WHERE id = ?",
        (note_id,)
    )
    note = cursor.fetchone()
    conn.close()
    
    if not note:
        raise HTTPException(status_code=404, detail="Nota non trovata")
        
    return dict(note)

@router.patch("/notes/{note_id}")
def update_note_transcription(note_id: str, payload: UpdateTranscriptionPayload):
    """Salva la trascrizione corretta a mano dall'utente nel DetailModal.
    Il titolo viene ricalcolato automaticamente dal nuovo testo."""
    updated_note = update_note_text(note_id, payload.extracted_text)

    if updated_note is None:
        raise HTTPException(status_code=404, detail="Nota non trovata")

    return updated_note

@router.get("/notes/{note_id}/file")
def download_original_file(note_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()
    conn.close()
    
    if not note:
        raise HTTPException(status_code=404, detail="Record nota non trovato nel database")
        
    filepath = os.path.join(UPLOAD_DIR, note["filename"])
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File originale non trovato sul disco")
        
    return FileResponse(filepath)

@router.delete("/notes/{note_id}")
def delete_note_route(note_id: str):
    deleted = delete_note(note_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Nota non trovata")

    return {
        "id": note_id,
        "status": "eliminato",
        "message": "Nota eliminata con successo"
    }

@router.get("/search")
def search_notes(q: str = Query(..., min_length=2)):
    hits = query_notes(q)
    return {
        "query": q,
        "total_hits": len(hits),
        "results": hits
    }