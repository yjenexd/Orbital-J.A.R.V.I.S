import Box from '@mui/material/Box'
import './App.css'
import AppLayout from './components/AppLayout'

function App() {
  return (
    <Box sx={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppLayout />
    </Box>
  )
}

export default App