import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Box from '@mui/material/Box'
import CircularProgress from '@mui/material/CircularProgress'
import './App.css'
import AppLayout from './components/AppLayout'
import LoginPage from './components/LoginPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import CalendarPage from './pages/CalendarPage'
import DashboardPage from './pages/DashboardPage'
import ProfilePage from './pages/ProfilePage'

function AppRoutes() {
  const { session, loading } = useAuth()

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'grid',
          placeItems: 'center',
        }}
      >
        <Box
          sx={{
            width: 72,
            height: 72,
            borderRadius: '20px',
            bgcolor: 'rgba(255,255,255,0.92)',
            border: '1px solid #e1e7f2',
            display: 'grid',
            placeItems: 'center',
            boxShadow: '0 18px 38px -30px rgba(46, 69, 114, 0.45)',
          }}
        >
          <CircularProgress size={28} sx={{ color: '#5a6df0' }} />
        </Box>
      </Box>
    )
  }

  if (!session) {
    return <LoginPage />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

function App() {
  return (
    <AuthProvider>
      <Box sx={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppRoutes />
      </Box>
    </AuthProvider>
  )
}

export default App
