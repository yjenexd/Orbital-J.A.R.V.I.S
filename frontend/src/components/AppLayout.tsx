import { useLocation, useNavigate, Outlet } from 'react-router-dom'
import { Box, CssBaseline, GlobalStyles, Tabs, Tab, Avatar, Typography } from '@mui/material'

const TABS = [
  { label: 'Dashboard', path: '/' },
  { label: 'Calendar', path: '/calendar' },
  { label: 'Profile', path: '/profile' },
]

export default function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()

  const currentTab = TABS.findIndex((t) => t.path === location.pathname)
  const activeTab = currentTab === -1 ? 0 : currentTab

  return (
    <>
      <CssBaseline />
      <GlobalStyles
        styles={{
          'html, body, #root': {
            height: '100vh',
            margin: 0,
          },
        }}
      />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100%', px: { xs: 1.25, sm: 2 }, pb: { xs: 1.25, sm: 2 } }}>
        <Box
          sx={{
            mt: { xs: 1, sm: 1.5 },
            mb: { xs: 1.25, sm: 1.5 },
            px: { xs: 1.25, sm: 1.6 },
            py: 1,
            borderRadius: '16px',
            backgroundColor: 'rgba(255,255,255,0.88)',
            border: '1px solid #e2e8f3',
            boxShadow: '0 16px 38px -28px rgba(46, 69, 114, 0.45)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              component="img"
              src="/jarvis-logo.png"
              alt="JARVIS icon"
              sx={{ width: 28, height: 28, borderRadius: '8px', objectFit: 'cover', border: '1px solid #d3dcf0', bgcolor: '#eef2ff' }}
            />
            <Typography sx={{ fontWeight: 700, fontSize: '0.98rem', letterSpacing: '-0.02em', color: '#1e2a42' }}>
              J².A.R.V.I.S
            </Typography>
          </Box>

          <Tabs
            value={activeTab}
            onChange={(_, newValue) => navigate(TABS[newValue].path)}
            sx={{
              minHeight: 40,
              '.MuiTabs-indicator': {
                height: 3,
                borderRadius: 99,
                backgroundColor: '#5a6df0',
              },
              '.MuiTab-root': {
                minHeight: 40,
                textTransform: 'none',
                px: { xs: 1.25, sm: 2 },
                minWidth: 'auto',
                color: '#67748d',
                fontSize: '0.9rem',
                fontWeight: 600,
              },
              '.Mui-selected': {
                color: '#2a3553 !important',
              },
            }}
          >
            {TABS.map((t) => (
              <Tab key={t.path} label={t.label} />
            ))}
          </Tabs>

          <Box sx={{ ml: 'auto' }}>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                bgcolor: '#dbe3ff',
                color: '#36457e',
                fontSize: '0.85rem',
                fontWeight: 700,
                border: '1px solid #c8d5ff',
              }}
            >
              AI
            </Avatar>
          </Box>
        </Box>

        <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
          <Outlet />
        </Box>
      </Box>
    </>
  )
}
