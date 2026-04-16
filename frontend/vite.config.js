import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite dev server proxies /predict and /health to the FastAPI backend on :8000
// so the browser sees a single origin (no CORS setup needed in dev).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/predict': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
