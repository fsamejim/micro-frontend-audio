import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'dashboardMf',
      filename: 'remoteEntry.js',
      exposes: {
        './App': './src/App.tsx',
        './Dashboard': './src/components/Dashboard.tsx',
        './UserProfile': './src/components/UserProfile.tsx',
        './Statistics': './src/components/Statistics.tsx',
      },
      shared: ['react', 'react-dom']
    }),
  ],
  server: {
    port: 3004,
    cors: {
      origin: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002', 'http://localhost:3003'],
      credentials: true,
    },
  },
  build: {
    target: 'esnext',
  },
})
