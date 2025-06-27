import React, { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { Loading } from './components/Loading'
import './App.css'

// Lazy load microfrontends
const AuthLogin = React.lazy(() => import('authMf/Login'))
const AuthRegister = React.lazy(() => import('authMf/Register'))
const AuthTest = React.lazy(() => import('authMf/Test'))

function App() {
  return (
    <Router>
      <div className="shell-app">
        <Navbar />
        <main className="shell-content">
          <Suspense fallback={<Loading />}>
            <Routes>
              <Route path="/auth" element={<Navigate to="/auth/login" replace />} />
              <Route path="/auth/login" element={<AuthLogin />} />
              <Route path="/auth/register" element={<AuthRegister />} />
              <Route path="/auth/test" element={<AuthTest />} />
              <Route path="/" element={<Navigate to="/auth/login" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  )
}

export default App
