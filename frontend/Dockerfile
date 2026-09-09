# Usiamo un'immagine Node.js leggera basata su Alpine Linux
FROM node:20-alpine

# Impostiamo la directory di lavoro
WORKDIR /app

# Copiamo prima i file delle dipendenze per sfruttare la cache di Docker
# (questi file verranno generati quando inizializzeremo il progetto)
COPY package*.json ./

# Installiamo le dipendenze
RUN npm install

# Copiamo il resto del codice del frontend
COPY . .

# Esponiamo la porta 3000 (quella definita nel docker-compose.yml)
EXPOSE 3000

# Avviamo il server di sviluppo Vite, esponendolo sulla rete di Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]