import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // If running inside Docker, connect to backend container 'backend:8000'
  const backendTarget = process.env.BACKEND_URL || env.BACKEND_URL || 'http://backend:8000'
  const wsTarget = process.env.BACKEND_WS_URL || env.BACKEND_WS_URL || 'ws://backend:8000'

  return {
    plugins: [react()],
    server: {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        },
        '/ws': {
          target: wsTarget,
          ws: true,
        }
      }
    }
  }
})
