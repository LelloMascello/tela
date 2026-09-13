# TELA (Text Extraction & Local Archiving)

TELA è un sistema self-hosted progettato per centralizzare, elaborare e indicizzare appunti personali e documenti. Fornisce una pipeline completa per acquisire file in vari formati, estrarne il contenuto testuale e renderli immediatamente ricercabili tramite un motore full-text locale.

## Architettura del Sistema

Il progetto è suddiviso nei seguenti moduli:
- **Acquisizione Dati:** Upload via Web App da dispositivi mobili o desktop e tramite chatbot Telegram.
- **Backend (API & Elaborazione):** Python (FastAPI).
- **Motore di Estrazione Multi-Formato:** 
  - OCR locale (EasyOCR) per immagini di appunti manoscritti.
  - Estrazione testuale nativa per PDF, documenti Word/TXT/PowerPoint/Excel.
  - Trascrizione audio per formati audio e video mp3/mp4/avi
- **Archiviazione e Ricerca:** SQLite (metadati e storage file) e MeiliSearch (motore di ricerca fuzzy).
- **Frontend:** Web application per visualizzazione, ricerca, download e confronto documento/testo.

## Funzionalità Principali

- **Supporto Multi-Formato:** Caricamento di file immagine (.png, .jpg e .jpeg), PDF, documenti (.docx), file di testo (.txt), presentazioni (.pptx), fogli di calcolo (.xlsx), audio (.mp3 e .wav) e video (.mp4 e .avi).
- **Elaborazione Smart:** Il sistema riconosce il formato e applica automaticamente l'OCR alle immagini o l'estrazione testo ai documenti digitali e Faster-Whisper per formati audio e video.
- **Titolo automatico:** ogni nota mostra un titolo generato in automatico dai primi 30 caratteri del testo estratto (con puntini di sospensione se più lungo), al posto del nome file casuale. Visibile sia sul sito (card e dettaglio) sia su Telegram (risultati di ricerca e conferma di upload).
- **Modifica trascrizione:** il testo estratto può essere corretto a mano dal DetailModal quando l'OCR o la trascrizione audio contengono errori; il titolo automatico viene ricalcolato alla stessa maniera dopo il salvataggio.
- **Interfaccia di Visualizzazione:** Affiancamento o sovrapposizione tra il documento originale (mantenuto intatto per il download) e la versione digitalizzata.
- **Ricerca Avanzata:** Fuzzy search integrata su tutto il testo estratto per recuperare rapidamente le informazioni, tollerando errori di battitura.
- **Tela archive bot:** un bot telegram che permette di caricare e ricercare file senza essere sulla stessa LAN del server.

## Setup e Installazione
```
tela/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point minimo (CORS, startup e inclusione dei router)
│   │   ├── api/
│   │   │   └── routes.py        # Tutti gli endpoint (upload, notes, ricerca, modifica trascrizione)
│   │   ├── core/
│   │   │   ├── config.py        # Variabili globali (UPLOAD_DIR, chiavi Meili etc.)
│   │   │   └── database.py      # Init SQLite/MeiliSearch, CRUD note (testo, titolo automatico, status)
│   │   └── services/
│   │       ├── extractor.py     # Estrazione testo (OCR, PDF, Docx, TXT)
│   │       └── search.py        # Logica di MeiliSearch (inserimento, indicizzazione e query)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                 # Interfaccia Utente (React/Vue)
│   ├── public/               # Asset statici
│   ├── src/
│   │   ├── components/       # Componenti riutilizzabili (es. NoteCard, SearchBar)
│   │   ├── assets/           # elementi grafici
│   │   ├── api/              # Funzioni per comunicare con il backend (axios)
│   │   └── App.vue           # Root component
│   ├── package.json          # Dipendenze Node.js
│   └── Dockerfile            # Istruzioni di build per il frontend
│
├── bot/                                       
│   ├── app/                                
│   │   ├── core/                
│   │   │   └── config.py                           
│   │   ├── handlers/            
│   │   │   ├── auth.py           
│   │   │   ├── search.py           
│   │   │   ├── site.py          
│   │   │   ├── start.py            
│   │   │   └── upload.py        
│   │   ├── main.py             
│   │   └── client.py    
│   ├── requirements.txt            
│   └── Dockerfile           
│
├── data/                     # Dati persistenti (da inserire nel .gitignore)
│   ├── uploads/              # Salvataggio delle immagini ricevute
│   ├── database/             # File SQLite
│   └── meili_data/           # Volumi del motore di ricerca
│
├── docker-compose.yml        # Orchestratore per far girare Backend, Frontend e MeiliSearch
├── .env.example              # Template delle variabili d'ambiente (sicuro da committare)
├── .gitignore                # Regole di esclusione file
└── README.md                 # Documentazione del progetto
```

## TO DO

**Esportazione in massa di file**
- aggiungere sia su telegram che su web un pulsante che permetta di scaricare le i file o le trascrizioni di tutti i file risultanti da una ricerca in blocco in uno .zip

**Integrazione Gemini Notebook (ex NotebookLM)**
- Aggiungere una libreria Python non ufficiale (es. `notebooklm-py`) per interfacciarsi con le API interne di Gemini Notebook tramite cookie di sessione (da configurare nel .env).
- questo per implementare la logica per creare automaticamente un nuovo notebook utilizzando le trascrizioni (`extracted_text`), dei file risultanti da una ricerca,come fonti di testo (`textContent`), usando il titolo automatico come `displayName` della fonte. 
- Aggiungere un trigger per questa esportazione (pulsante sulla Web App).