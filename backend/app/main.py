from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TELA Backend",
    description="API per Text Extraction & Local Archiving (PENNA project)",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "TELA Backend è online e operativo sul Pi 5!"}

@app.post("/api/upload")
async def upload_note(file: UploadFile = File(...)):
    # 1. Salvataggio dell'immagine nella cartella /data/uploads/
    # 2. Scrittura del record iniziale su SQLite
    # 3. Invio dell'immagine al motore EasyOCR
    
    return {
        "filename": file.filename, 
        "status": "ricevuto",
        "message": "Pronto per l'elaborazione OCR"
    }