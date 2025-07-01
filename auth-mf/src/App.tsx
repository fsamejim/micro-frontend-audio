import { ThemeProvider, CssBaseline } from '@mui/material'
import { createTheme } from '@mui/material/styles'
import { AuthProvider } from './contexts/AuthContext'
import { Login } from './components/auth/Login'
import './App.css'

const theme = createTheme()

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <div className="auth-mf-container">
          <Login />
        </div>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
