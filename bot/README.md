# TELA Bot — Guida di creazione e deploy

Bot Telegram per TELA: carica appunti/documenti, li cerca e reindirizza al frontend, senza dover essere connessi alla VPN per farlo (il bot parla con Telegram in uscita; solo il tuo telefono deve raggiungere Telegram, non il tuo Pi).

## 1. Crea il bot con BotFather

1. Apri Telegram e cerca **@BotFather** (account verificato, ✅ blu).
2. Manda `/newbot`.
3. Scegli un **nome visualizzato** (es. `TELA Archive`) — può contenere spazi, lo vede solo l'utente.
4. Scegli uno **username** univoco che termini in `bot` (es. `tela_archive_bot`) — è l'identificativo pubblico.
5. BotFather risponde con un messaggio contenente il **token**, qualcosa come:
   ```
   123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
   ```
   Questo token è equivalente a una password: chiunque lo possieda può controllare il bot. Non committarlo mai nel repository.

### Opzionale ma consigliato: rifinitura del bot

Sempre a BotFather:
- `/setdescription` — testo mostrato nella schermata "Avvia" prima del primo messaggio.
- `/setabouttext` — testo mostrato nel profilo del bot.
- `/setuserpic` — un'icona (es. il logo di TELA).
- `/setcommands` — registra i comandi per farli comparire nel menu "/" di Telegram:
  ```
  start - Mostra il messaggio di benvenuto
  help - Mostra i comandi disponibili
  cerca - Cerca nei documenti archiviati
  sito - Apri l'interfaccia web di TELA
  ```

## 2. Trova il tuo Telegram user ID

Serve per limitare l'uso del bot al solo proprietario dell'archivio (`ALLOWED_USER_IDS`).

1. Cerca **@userinfobot** (o **@RawDataBot**) su Telegram.
2. Avvialo: risponde subito con il tuo `Id` numerico (es. `987654321`).
3. Se più persone della famiglia devono poter usare il bot, ripeti per ognuna e separa gli ID con virgola nel passo successivo.

## 3. Configura le variabili d'ambiente

Nella cartella principale del progetto (dove sta `docker-compose.yml`), apri o crea il file `.env` e aggiungi:

```bash
# --- Bot Telegram ---
TELEGRAM_BOT_TOKEN=123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
WEBSITE_URL=http://IP_DEL_PI:3000        # o l'URL/IP VPN del frontend
ALLOWED_USER_IDS=987654321               # più ID separati da virgola: 987654321,111222333
```

`docker compose` legge automaticamente `.env` dalla stessa cartella del `docker-compose.yml`, quindi non serve altra configurazione: le variabili `${TELEGRAM_BOT_TOKEN}` ecc. nel compose vengono sostituite al volo.

⚠️ Assicurati che `.env` sia elencato nel `.gitignore` principale del repository (accanto a `data/`), così il token non finisce mai su GitHub.

## 4. Build e avvio

Dalla cartella principale del progetto:

```bash
docker compose up -d --build bot
```

(oppure `docker compose up -d --build` per ricostruire tutto lo stack insieme). Controlla i log per verificare che si sia connesso a Telegram senza errori:

```bash
docker compose logs -f bot
```

Dovresti vedere `Avvio TELA bot (long polling)...` senza eccezioni successive.

## 5. Provalo

Nella chat con il tuo bot su Telegram:
- `/start` — messaggio di benvenuto e lista comandi.
- Invia un PDF, un `.docx` o una foto di un appunto → il bot lo carica su TELA e risponde con l'`id` e lo stato.
- `/cerca riunione lunedì` → il bot mostra i risultati come pulsanti; toccane uno per ricevere il file.
- `/sito` → il bot risponde con il link al frontend.

Se invii il bot a un altro account Telegram non presente in `ALLOWED_USER_IDS`, riceverà "⛔ Non sei autorizzato a usare questo bot." — è il comportamento atteso.

## 6. (Opzionale) Pulsante menu verso il sito

Oltre al comando `/sito`, puoi impostare un pulsante persistente accanto alla casella di testo che apre direttamente il frontend:

1. A BotFather: `/mybots` → seleziona il bot → **Bot Settings** → **Menu Button** → **Configure menu button**.
2. Inserisci l'URL del frontend (deve essere raggiungibile dal telefono, quindi via VPN se il Pi non è esposto pubblicamente — coerente con l'architettura attuale) e un'etichetta come "Apri TELA".

## Limiti da tenere presenti

- **Dimensione file:** l'API Bot standard di Telegram permette al bot di **scaricare** file inviati dagli utenti fino a **20MB**. Va bene per scansioni, PDF e la maggior parte degli audio; file video/audio più pesanti falliranno con un messaggio d'errore esplicito dal bot. Per alzare il limite (fino a 2GB) servirebbe un [Bot API server locale](https://github.com/tdlib/telegram-bot-api) — non incluso qui, da valutare solo se ne senti davvero il bisogno.
- **Foto vs file:** le foto inviate come "Foto" vengono ricompresse da Telegram (qualità inferiore per l'OCR). Il bot lo ricorda all'utente ma le carica comunque; meglio inviare scansioni come "File".
- **Polling vs webhook:** questo bot usa il *long polling* (`run_polling`), non un webhook — è la scelta corretta qui perché non richiede di esporre il Pi su Internet: il container si connette in uscita ai server Telegram.

## Struttura del codice

```
bot/
├── app/
│   ├── main.py             # costruisce l'Application e avvia il polling
│   ├── client.py           # client HTTP verso le API REST del backend TELA
│   ├── core/
│   │   └── config.py       # lettura variabili d'ambiente, logging
│   └── handlers/
│       ├── auth.py         # decorator @restricted (controllo ALLOWED_USER_IDS)
│       ├── start.py        # /start, /help
│       ├── upload.py       # gestione documenti e foto in arrivo
│       ├── search.py       # /cerca + pulsanti inline di download
│       └── site.py         # /sito
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

Il bot **non implementa logica propria di estrazione/ricerca**: chiama semplicemente gli endpoint già esistenti in `backend/app/api/routes.py` (`/api/upload`, `/api/search`, `/api/notes/{id}/file`), esattamente come farebbe il frontend web.

## Troubleshooting

| Sintomo | Causa probabile |
|---|---|
| Il bot non risponde a nulla | Token errato/mancante in `.env`, oppure il container non è partito — controlla `docker compose logs -f bot` |
| `Unauthorized` nei log | `TELEGRAM_BOT_TOKEN` sbagliato o rigenerato da BotFather nel frattempo |
| "⛔ Non sei autorizzato" per il tuo stesso account | Il tuo user ID non è (correttamente) in `ALLOWED_USER_IDS` — ricontrolla con @userinfobot |
| "❌ Caricamento fallito" | Il backend ha risposto con un errore — controlla `docker compose logs -f backend` |
| "⚠️ File troppo grande" | Il file supera il limite di 20MB per il download lato bot (vedi sopra) |
