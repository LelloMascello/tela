import axios from 'axios';

// Base URL del backend, letta da VITE_BACKEND_URL (vedi .env).
// Fallback a localhost per sviluppo locale senza Docker.
export const api = axios.create({
  baseURL: `${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api`,
});