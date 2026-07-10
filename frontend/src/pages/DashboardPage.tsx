import { Box } from '@mui/material'
import { ChatInterface } from '../components/ChatInterface'
import { DailyBriefing } from '../components/DailyBriefing'
import { DashboardSummary } from '../components/DashboardSummary'
import { TaskPanel } from '../components/TaskPanel'
import { SchedulePanel } from '../components/SchedulePanel'

export default function DashboardPage() {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', lg: '1fr 390px' },
        flex: 1,
        minHeight: 0,
        gap: { xs: 1.25, sm: 1.5 },
      }}
    >
      <Box
        component="main"
        sx={{
          minHeight: 0,
          overflow: 'auto',
          display: 'grid',
          gridTemplateRows: 'auto auto 1fr',
          gap: { xs: 1.25, sm: 1.5 },
          pr: { lg: 0.5 },
        }}
      >
        <DashboardSummary />
        <DailyBriefing />

        <Box
          sx={{
            minHeight: 0,
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: { xs: 1.25, sm: 1.5 },
            alignItems: 'start',
          }}
        >
          <TaskPanel />
          <SchedulePanel />
        </Box>
      </Box>

      <Box
        component="aside"
        sx={{
          minHeight: 0,
          overflow: 'hidden',
          display: 'flex',
        }}
      >
        <ChatInterface />
      </Box>
    </Box>
  )
}
