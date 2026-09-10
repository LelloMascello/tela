# TELA (Text Extraction & Local Archiving)

TELA è un sistema self-hosted progettato per centralizzare, elaborare e indicizzare appunti personali e documenti. Fornisce una pipeline completa per acquisire file in vari formati, estrarne il contenuto testuale e renderli immediatamente ricercabili tramite un motore full-text locale.

## Architettura del Sistema

Il progetto è suddiviso nei seguenti moduli:
- **Acquisizione Dati:** Upload via Web App da dispositivi mobili o desktop.
- **Backend (API & Elaborazione):** Python (FastAPI).
- **Motore di Estrazione Multi-Formato:** 
  - OCR locale (EasyOCR) per immagini di appunti manoscritti.
  - Estrazione testuale nativa per PDF e documenti Word/TXT.
- **Archiviazione e Ricerca:** SQLite (metadati e storage file) e MeiliSearch (motore di ricerca fuzzy).
- **Frontend:** Web application per visualizzazione, ricerca, download e confronto documento/testo.

## Funzionalità Principali

- **Supporto Multi-Formato:** Caricamento di file immagine (PNG, JPG), PDF, Word (.docx) e file di testo (.txt).
- **Elaborazione Smart:** Il sistema riconosce il formato e applica automaticamente l'OCR alle immagini o l'estrazione testo ai documenti digitali.
- **Interfaccia di Visualizzazione:** Affiancamento o sovrapposizione tra il documento originale (mantenuto intatto per il download) e la versione digitalizzata.
- **Ricerca Avanzata:** Fuzzy search integrata su tutto il testo estratto per recuperare rapidamente le informazioni, tollerando errori di battitura.

## Setup e Installazione
```
tela/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point minimo (CORS, startup e inclusione dei router)
│   │   ├── api/
│   │   │   └── routes.py        # Tutti gli endpoint (@router.post, @router.get)
│   │   ├── core/
│   │   │   ├── config.py        # Variabili globali (UPLOAD_DIR, chiavi Meili etc.)
│   │   │   └── database.py      # Script per inizializzare SQLite e MeiliSearch
│   │   └── services/
│   │       ├── extractor.py     # Estrazione testo (OCR, PDF, Docx, TXT)
│   │       └── search.py        # Logica di MeiliSearch (inserimento, indicizzazione e query)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                 # Interfaccia Utente (React/Vue)
│   ├── public/               # Asset statici
│   ├── src/
│   │   ├── components/       # Componenti riutilizzabili (es. ImageTextSlider, SearchBar)
│   │   ├── views/            # Pagine (es. Dashboard, NoteViewer)
│   │   ├── api/              # Funzioni per comunicare con il backend
│   │   └── App.jsx/vue       # Root component
│   ├── package.json          # Dipendenze Node.js
│   └── Dockerfile            # Istruzioni di build per il frontend
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

futuri sviluppi per il progetto:
- **ampliamento formati supportati:** tracce audio e video formati mp4 e mp3, PowerPoint e excel
- **caricamento:** cambiare il metodo di caricamento da sito a bot telegram, questo per evitare di doversi sempre connettere alla vpn per caricare.
- **eliminazione:** aggiungere alla copia di pulsanti scarica e visualizza testo estratto un terzo pulsante per cancellare l'elemento.
- **ricerca:** permettere la ricerca tramite Telegram che ritorna i file più pertinenti da scaricare