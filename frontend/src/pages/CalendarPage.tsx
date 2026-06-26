import { Box } from '@mui/material'
import { CalendarView } from '../components/CalendarView'

export default function CalendarPage() {
  return (
    <Box sx={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
      <CalendarView />
    </Box>
  )
}
