import { Box } from '@mui/material';
import { ChatInterface } from '../components/ChatInterface';
import { DailyBriefing } from '../components/DailyBriefing';
import { TaskPanel } from '../components/TaskPanel';
import { SchedulePanel } from '../components/SchedulePanel';

export default function DashboardPage() {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: '65% 35%' },
        gridTemplateRows: { xs: 'auto 1fr', md: '1fr' },
        flex: 1,
        minHeight: 0,
      }}
    >
      <Box
        component="main"
        sx={{
          p: 3,
          bgcolor: 'background.default',
          minHeight: 0,
          overflow: 'hidden',
          display: 'grid',
          gridTemplateRows: 'auto 1fr',
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
        <ChatInterface />
      </Box>
    </Box>
  );
}
