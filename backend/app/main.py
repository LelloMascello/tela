from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="TELA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_dbs():
    # 1. Connessione e creazione tabella 'notes' in SQLite (id, filename, status, extracted_text)
    # 2. Connessione a MeiliSearch e inizializzazione dell'indice 'notes'
    pass

def process_note_background(note_id: str, filepath: str, file_extension: str):
    # 1. Routing dell'estrazione in base a file_extension (txt, pdf, docx, jpg/png)
    # 2. Esecuzione EasyOCR, PyMuPDF, o python-docx per estrarre il testo
    # 3. Aggiornamento in SQLite del campo 'extracted_text' e status='completato'
    # 4. Invio dell'ID e del testo estratto a MeiliSearch
    # 5. Gestione delle eccezioni (impostazione status='errore' in SQLite)
    pass

@app.on_event("startup")
def startup_event():
    # Avvia la funzione di setup dei database quando il server si accende
    init_dbs()

@app.get("/")
def health_check():
    # Ritorna lo stato operativo del server
    pass

@app.post("/api/upload")
async def upload_note(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. Valida l'estensione del file
    # 2. Genera un ID univoco (UUID) e salva il file originale su disco
    # 3. Salva un nuovo record in SQLite con status='in_elaborazione'
    # 4. Avvia process_note_background come BackgroundTask
    # 5. Ritorna l'ID generato per confermare l'upload al frontend
    pass

@app.get("/api/notes")
def list_notes(limit: int = 50, offset: int = 0):
    # 1. Interroga SQLite per ottenere gli appunti recenti
    # 2. Ritorna un array di documenti paginati (per la dashboard del frontend)
    pass

@app.get("/api/notes/{note_id}")
def get_note_details(note_id: str):
    # 1. Cerca il singolo appunto su SQLite tramite ID
    # 2. Ritorna i metadati completi e il testo estratto (utile per la vista con lo slider)
    pass

@app.get("/api/notes/{note_id}/file")
def download_original_file(note_id: str):
    # 1. Cerca il nome del file originale su SQLite tramite ID
    # 2. Verifica che il file esista nella cartella uploads
    # 3. Usa FileResponse per servire il file (PDF, Docx, o Immagine)
    pass

@app.get("/api/search")
def search_notes(q: str = Query(...)):
    # 1. Inoltra la stringa 'q' a MeiliSearch per la fuzzy search
    # 2. Ricevi gli ID dei documenti pertinenti
    # 3. (Opzionale) Recupera i nomi dei file da SQLite usando gli ID trovati
    # 4. Ritorna i risultati al frontend
    pass