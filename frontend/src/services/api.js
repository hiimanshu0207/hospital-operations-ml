/**
 * API service layer.
 *
 * Centralizes all HTTP calls to the FastAPI backend.
 * Uses axios for consistent error handling and interceptors.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Check backend health status.
 * @returns {Promise<{status: string, app: string, version: string}>}
 */
export const checkHealth = () => api.get('/health').then((res) => res.data)

export default api
