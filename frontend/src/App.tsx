import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Box from '@mui/material/Box';
import './App.css';
import AppLayout from './components/AppLayout';
import DashboardPage from './pages/DashboardPage';
import CalendarPage from './pages/CalendarPage';
import ProfilePage from './pages/ProfilePage';

function App() {
  return (
    <Box sx={{ width: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="profile" element={<ProfilePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </Box>
  );
}

export default App;
