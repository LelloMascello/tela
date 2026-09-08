# TELA (Text Extraction & Local Archiving)

TELA è un sistema self-hosted progettato per digitalizzare, elaborare e indicizzare appunti scritti a mano. Fornisce una pipeline completa dal dispositivo di acquisizione analogico a un archivio digitale ricercabile, centralizzato su un server locale (Raspberry Pi 5).

## Architettura del Sistema

Il progetto è suddiviso nei seguenti moduli:
- **Acquisizione Dati:** Huion Note X10 e Smartphone (tramite app ufficiale).
- **Backend (API & Elaborazione):** Python (FastAPI).
- **Motore OCR:** Modello locale di riconoscimento della scrittura a mano (HTR).
- **Archiviazione e Ricerca:** SQLite (metadati) e MeiliSearch (motore di ricerca fuzzy full-text).
- **Frontend:** Web application (React/Vue.js) per l'interazione utente.

## Funzionalità Principali

- **Caricamento:** Endpoint dedicato per l'upload degli appunti acquisiti dal dispositivo mobile.
- **Elaborazione OCR:** Conversione automatica della scrittura a mano in testo formattato.
- **Interfaccia di Confronto:** Visualizzazione simultanea della versione manoscritta e di quella digitalizzata tramite slider interattivo.
- **Ricerca Avanzata:** Fuzzy search integrata su tutto il testo estratto per il recupero rapido delle informazioni.
- **Gestione File:** Funzionalità di visualizzazione e download degli appunti.

## Setup e Installazione
*(In via di definizione)*