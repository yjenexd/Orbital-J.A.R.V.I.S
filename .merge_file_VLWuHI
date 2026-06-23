import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import './App.css'
import AppLayout from './components/AppLayout'
import LoginPage from './components/LoginPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function AppContent() {
  const { session, loading } = useAuth()

  if (loading) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    )
  }

  return session ? <AppLayout /> : <LoginPage />
}

function App() {
  return (
    <AuthProvider>
      <Box sx={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppContent />
      </Box>
    </AuthProvider>
  )
}

export default App
