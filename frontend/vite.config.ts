import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/process': { target: 'http://localhost:8000', changeOrigin: true },
      '/submit': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/samples': { target: 'http://localhost:8000', changeOrigin: true },
      '/dataset': { target: 'http://localhost:8000', changeOrigin: true },
    }
  }
})
