import React, { Suspense } from 'react'
import './App.css'

// Lazy load microfrontends
const AuthTest = React.lazy(() => import('authMf/Test'))

function App() {
  return (
    <div className="shell-app">
      <h1>Shell App - Testing Module Federation</h1>
      <div style={{ border: '2px solid red', padding: '20px', margin: '20px' }}>
        <h2>Loading Remote Component:</h2>
        <Suspense fallback={<div>Loading auth component...</div>}>
          <AuthTest />
        </Suspense>
      </div>
    </div>
  )
}

export default App
