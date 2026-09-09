import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse

# Importazioni (commentate per ora) dai moduli service e core
# from core.config import UPLOAD_DIR
# from core.database import get_db_connection
# from services.extractor import process_note_background
# from services.search import query_notes

router = APIRouter(prefix="/api", tags=["Notes"])

@router.post("/upload")
async def upload_note(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1].lower()
    allowed_extensions = ['txt', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'webp']
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Formato non supportato")

    note_id = str(uuid.uuid4())
    safe_filename = f"{note_id}.{file_extension}"
    
    # 1. Utilizzare UPLOAD_DIR da core.config per comporre il percorso
    # filepath = os.path.join(UPLOAD_DIR, safe_filename)
    
    # 2. Salvare fisicamente il file con shutil
    
    # 3. Connettersi a SQLite (tramite core.database) e fare l'INSERT 
    # dello stato 'in_elaborazione'
    
    # 4. Aggiungere il task in background dal modulo services.extractor
    # background_tasks.add_task(process_note_background, note_id, filepath, file_extension)

    return {
        "id": note_id,
        "status": "in_elaborazione",
        "message": f"File {file_extension} salvato. Estrazione avviata."
    }

@router.get("/notes")
def list_notes(limit: int = 50, offset: int = 0):
    # 1. Connettersi a SQLite (tramite core.database)
    # 2. Eseguire SELECT * FROM notes ORDER BY id LIMIT ? OFFSET ?
    # 3. Restituire la lista dei documenti per popolare la dashboard
    pass

@router.get("/notes/{note_id}")
def get_note_details(note_id: str):
    # 1. Eseguire SELECT su SQLite filtrando per note_id
    # 2. Se non esiste, lanciare HTTPException 404
    # 3. Restituire i metadati e il testo estratto per la visualizzazione con slider
    pass

@router.get("/notes/{note_id}/file")
def download_original_file(note_id: str):
    # 1. Recuperare il filename da SQLite
    # 2. Comporre il filepath esatto (UPLOAD_DIR + filename)
    # 3. Verificare se esiste fisicamente (os.path.exists)
    # 4. Restituire il file tramite FileResponse(filepath)
    pass

@router.get("/search")
def search_notes(q: str = Query(..., min_length=2)):
    # 1. Chiamare la funzione query_notes(q) dal modulo services.search
    # 2. Ricevere gli ID trovati da MeiliSearch
    # 3. (Opzionale ma consigliato) Chiedere a SQLite i dettagli completi degli appunti trovati
    # 4. Restituire la lista combinata al frontend
    pass