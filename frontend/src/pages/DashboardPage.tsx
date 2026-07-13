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
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
        height: '100%',
        gap: { xs: 1.25, sm: 1.5 },
      }}
    >
      {/* Main content: left column + chat */}
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
          <TaskPanel />
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

      {/* 24-hour timeline pinned to the bottom */}
      <SchedulePanel />
    </Box>
  )
}
