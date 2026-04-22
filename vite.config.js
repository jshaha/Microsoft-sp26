import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
 
// https://vite.dev/config/
// Proxy /api/* -> FastAPI backend during dev. In production, set
// VITE_API_BASE at build time and the proxy becomes irrelevant.
const BACKEND = process.env.VITE_BACKEND_URL || 'http://localhost:8000'
 
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: BACKEND,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})