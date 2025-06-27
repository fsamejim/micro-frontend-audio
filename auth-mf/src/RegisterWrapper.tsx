import { ThemeProvider, CssBaseline } from '@mui/material'
import { createTheme } from '@mui/material/styles'
import { AuthProvider } from './contexts/AuthContext'
import { Register } from './components/auth/Register'
import './App.css'

const theme = createTheme()

function RegisterWrapper() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <div className="auth-mf-container">
          <Register />
        </div>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default RegisterWrapper