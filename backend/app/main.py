from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.database import init_dbs

app = FastAPI(
    title="TELA Backend",
    description="API per Text Extraction & Local Archiving",
    version="1.0.0"
)

# Configurazione CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Inizializza SQLite e MeiliSearch chiamando il modulo core
    init_dbs()

# Aggancia tutte le rotte definite in api/routes.py
app.include_router(router)

@app.get("/")
def health_check():
    return {"status": "TELA Backend Operativo"}