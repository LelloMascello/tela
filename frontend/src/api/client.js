import axios from 'axios';

// Puntiamo alla porta 8000 esposta dal backend nel docker-compose
export const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});