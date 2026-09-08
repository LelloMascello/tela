# Usiamo un'immagine ufficiale Python basata su Debian (ottima compatibilità per le librerie OCR)
FROM python:3.10-slim

# Impostiamo la cartella di lavoro all'interno del container
WORKDIR /app

# Installiamo le dipendenze di sistema necessarie per l'OCR e la gestione delle immagini
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiamo prima il file dei requisiti per sfruttare la cache di Docker
COPY requirements.txt .

# Installiamo le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamo il resto del codice del backend nella cartella di lavoro
COPY . .

# Esponghiamo la porta su cui girerà FastAPI
EXPOSE 8000

# Comando per avviare l'applicazione con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]