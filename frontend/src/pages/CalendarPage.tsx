import { Box } from '@mui/material';
import { CalendarView } from '../components/CalendarView';

export default function CalendarPage() {
  return (
    <Box sx={{ flex: 1, p: 3, bgcolor: 'background.default', overflowY: 'auto' }}>
      <CalendarView />
    </Box>
  );
}
