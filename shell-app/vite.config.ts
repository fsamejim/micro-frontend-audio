import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const isDocker = env.DOCKER_MODE === 'true'
  const isDev = mode === 'development'

  // Environment-aware remote URLs
  const getRemoteUrl = (port: number, service: string) => {
    if (isDocker) {
      // In Docker, services communicate via container names
      return `http://${service}:80/assets/remoteEntry.js`
    } else {
      // Local development uses localhost
      return `http://localhost:${port}/assets/remoteEntry.js`
    }
  }

  return {
    plugins: [
      react(),
      federation({
        name: 'shell-app',
        remotes: {
          authMf: getRemoteUrl(3002, 'auth-mf'),
          audioMf: getRemoteUrl(3003, 'audio-mf'),
          dashboardMf: getRemoteUrl(3004, 'dashboard-mf'),
        },
        shared: ['react', 'react-dom']
      }),
    ],
    server: {
      host: isDocker ? '0.0.0.0' : 'localhost', // Docker needs 0.0.0.0
      port: 3000,
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
