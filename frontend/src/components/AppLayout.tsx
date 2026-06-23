import { useLocation, useNavigate, Outlet } from 'react-router-dom';
import { Box, CssBaseline, GlobalStyles, Tabs, Tab } from '@mui/material';

const TABS = [
  { label: 'Dashboard', path: '/' },
  { label: 'Calendar', path: '/calendar' },
  { label: 'Profile', path: '/profile' },
];

export default function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  const currentTab = TABS.findIndex((t) => t.path === location.pathname);
  const activeTab = currentTab === -1 ? 0 : currentTab;

  return (
    <>
      <CssBaseline />
      <GlobalStyles
        styles={{
          'html, body, #root': {
            height: '100vh',
            margin: 0,
            overflow: 'hidden',
          },
        }}
      />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100%' }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => navigate(TABS[newValue].path)}
          sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}
        >
          {TABS.map((t) => (
            <Tab key={t.path} label={t.label} />
          ))}
        </Tabs>
        <Outlet />
      </Box>
    </>
  );
}
