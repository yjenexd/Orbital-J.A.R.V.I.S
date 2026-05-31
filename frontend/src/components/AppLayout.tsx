import { useState } from 'react';
import { Box, CssBaseline, GlobalStyles, Tabs, Tab } from '@mui/material';
import { ChatInterface } from './ChatInterface';
import { DailyBriefing } from './DailyBriefing';
import { TaskPanel } from './TaskPanel';
import { SchedulePanel } from './SchedulePanel';
import { CalendarView } from './CalendarView';

export default function AppLayout() {
  const [tab, setTab] = useState(0);

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

        {/* TOP: Tab bar */}
        <Tabs value={tab} onChange={(_, newValue) => setTab(newValue)} sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
          <Tab label="Dashboard" />
          <Tab label="Calendar" />
        </Tabs>

        {/* CONTENT */}
        {tab === 0 && (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '65% 35%' },
              gridTemplateRows: { xs: 'auto 1fr', md: '1fr' },
              flex: 1,
              minHeight: 0,
            }}
          >
            {/* LEFT: Dashboard column (isolated scroll area) */}
            <Box
              component="main"
              sx={{
                p: 3,
                bgcolor: 'background.default',
                minHeight: 0,        // important for child overflow to work inside a fixed-height parent
                overflow: 'hidden',
                display: 'grid',
                gridTemplateRows: 'auto 1fr', // hero row + scrollable content
                gap: 2,
              }}
            >
              <Box>
                <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1 }}>
                  <DailyBriefing />
                </Box>
              </Box>

              <Box
                sx={{
                  overflowY: 'auto',
                  minHeight: 0,
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
                  gap: 2,
                }}
              >
                <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, minHeight: 160 }}>
                  <TaskPanel />
                </Box>

                <Box sx={{ bgcolor: 'background.paper', p: 2, borderRadius: 1, minHeight: 160 }}>
                  <SchedulePanel />
                </Box>
              </Box>
            </Box>

            {/* RIGHT: Chat sidebar (sticky, independent scroll) */}
            <Box
              component="aside"
              sx={{
                bgcolor: 'background.paper',
                borderLeft: { md: 1 },
                borderColor: 'divider',
                minHeight: 0,
                position: { xs: 'relative', md: 'sticky' },
                top: 0,
                height: { xs: 'auto', md: '100%' },
                overflowY: 'auto',
                p: 2,
              }}
            >
              <Box>
                <ChatInterface />
              </Box>
            </Box>
          </Box>
        )}
        {tab === 1 && (
          <Box sx={{ flex: 1, p: 3, bgcolor: 'background.default', overflowY: 'auto' }}>
            <CalendarView />
          </Box>
        )}
      </Box>
    </>
  );
}