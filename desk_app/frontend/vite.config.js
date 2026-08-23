import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: true,       // Cloud Shell Web Preview proxies with its own hostname
    port: 5173,
    proxy: { '/api': 'http://localhost:8080' },
  },
})
