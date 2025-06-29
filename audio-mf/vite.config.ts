import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const isDocker = env.DOCKER_MODE === 'true'
  const isDev = mode === 'development'

  return {
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
      host: isDocker ? '0.0.0.0' : 'localhost', // Docker needs 0.0.0.0
      port: 3003,
      cors: true,
    },
    build: {
      target: 'esnext',
    },
    define: {
      // Make environment variables available to the app
      __DOCKER_MODE__: JSON.stringify(isDocker),
      __DEV_MODE__: JSON.stringify(isDev),
    }
  }
})
