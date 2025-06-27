import { ThemeProvider, CssBaseline } from '@mui/material'
import { createTheme } from '@mui/material/styles'
import { DashboardAuthProvider } from './contexts/AuthContext'
import { Dashboard } from './components/Dashboard'
import './App.css'

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DashboardAuthProvider>
        <div className="dashboard-mf-container">
          <Dashboard />
        </div>
      </DashboardAuthProvider>
    </ThemeProvider>
  )
}

export default App
