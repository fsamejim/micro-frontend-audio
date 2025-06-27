import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'audioMf',
      filename: 'remoteEntry.js',
      exposes: {
        './App': './src/App.tsx',
        './AudioUpload': './src/components/AudioUpload.tsx',
        './JobStatus': './src/components/JobStatus.tsx',
        './JobHistory': './src/components/JobHistory.tsx',
      },
      shared: ['react', 'react-dom']
    }),
  ],
  server: {
    port: 3003,
  },
  build: {
    target: 'esnext',
  },
})
