import React, { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { Loading } from './components/Loading'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuthState } from './hooks/useAuthState'
import './App.css'

// Lazy load microfrontends
const AuthLogin = React.lazy(() => import('authMf/Login'))
const AuthRegister = React.lazy(() => import('authMf/Register'))
const AudioApp = React.lazy(() => import('audioMf/App'))
const DashboardApp = React.lazy(() => import('dashboardMf/App'))

// Component to handle default route redirect
function DefaultRoute() {
  const { isAuthenticated } = useAuthState()
  return <Navigate to={isAuthenticated ? '/dashboard' : '/auth/login'} replace />
}

function App() {
  return (
    <Router>
      <div className="shell-app">
        <Navbar />
        <main className="shell-content">
          <Suspense fallback={<Loading />}>
            <Routes>
              {/* Public routes */}
              <Route path="/auth" element={<Navigate to="/auth/login" replace />} />
              <Route path="/auth/login" element={<AuthLogin />} />
              <Route path="/auth/register" element={<AuthRegister />} />

              {/* Protected routes */}
              <Route path="/audio" element={
                <ProtectedRoute>
                  <AudioApp />
                </ProtectedRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <DashboardApp />
                </ProtectedRoute>
              } />

              {/* Default route - redirect based on auth state */}
              <Route path="/" element={<DefaultRoute />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  )
}

export default App
