import { useState } from 'react'
import { ThemeProvider, CssBaseline, Container, Typography, Tabs, Tab, Box } from '@mui/material'
import { createTheme } from '@mui/material/styles'
import { AudioUpload } from './components/AudioUpload'
import { JobStatus } from './components/JobStatus'
import { JobHistory } from './components/JobHistory'
import { AudioAuthProvider } from './contexts/AuthContext'
import type { JobStatusResponse } from './types/translation'
import './App.css'

const theme = createTheme()

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

function App() {
  const [tabValue, setTabValue] = useState(0)
  const [currentJobId, setCurrentJobId] = useState<string>('')

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleJobCreated = (jobStatus: JobStatusResponse) => {
    setCurrentJobId(jobStatus.job_id)
    setTabValue(1) // Switch to Job Status tab
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AudioAuthProvider>
        <Container maxWidth="lg" sx={{ mt: 2 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Audio Translation Service
          </Typography>
          
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="audio processing tabs">
              <Tab label="Upload Audio" />
              <Tab label="Job Status" />
              <Tab label="Job History" />
            </Tabs>
          </Box>
          
          <TabPanel value={tabValue} index={0}>
            <AudioUpload onJobCreated={handleJobCreated} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <JobStatus jobId={currentJobId} />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <JobHistory />
          </TabPanel>
        </Container>
      </AudioAuthProvider>
    </ThemeProvider>
  )
}

export default App
