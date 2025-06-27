import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'authMf',
      filename: 'remoteEntry.js',
      exposes: {
        './App': './src/App.tsx',
        './Login': './src/LoginWrapper.tsx',
        './Register': './src/RegisterWrapper.tsx',
        './Test': './src/TestComponent.tsx',
      },
      shared: ['react', 'react-dom']
    }),
  ],
  server: {
    port: 3001,
  },
  build: {
    target: 'esnext',
  },
})
