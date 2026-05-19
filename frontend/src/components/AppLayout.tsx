import React from 'react';
import { Box, CssBaseline, GlobalStyles } from '@mui/material';
import { ChatInterface } from './ChatInterface';
import { DailyBriefing } from './DailyBriefing';
import { TaskPanel } from './TaskPanel';
import { SchedulePanel } from './SchedulePanel';

export default function AppLayout() {
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
          '#root > div': { height: '100%' },
        }}
      />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '65% 35%' },
          gridTemplateRows: { xs: 'auto 1fr', md: '1fr' },
          height: '100vh',
          width: '100%',
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

            <Box sx={{ gridColumn: '1 / -1', bgcolor: 'background.paper', p: 2, borderRadius: 1 }}>
              <h3>Wide Row</h3>
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
            height: { xs: 'auto', md: '100vh' },
            overflowY: 'auto',
            p: 2,
          }}
        >
            <Box>
                <ChatInterface />
            </Box> 
        </Box>
      </Box>
    </>
  );
}