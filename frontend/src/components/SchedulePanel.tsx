import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { CalendarMonth, Warning, Shield } from '@mui/icons-material';

interface ScheduleEvent {
  time: string;
  title: string;
  type: 'module' | 'meeting' | 'protected' | 'conflict';
}

export function SchedulePanel() {
  const events: ScheduleEvent[] = [
    { time: '09:00 AM', title: 'CS2040S - Data Structures', type: 'module' },
    { time: '11:00 AM', title: 'CS2030S - Programming Methodology', type: 'module' },
    { time: '02:00 PM', title: 'Project Meeting with Jason', type: 'conflict' },
    { time: '02:00 PM', title: 'Private Tuition Slot', type: 'conflict' },
    { time: '04:00 PM', title: 'MA1521 - Calculus', type: 'module' },
    { time: '08:00 PM', title: 'CS2040S Revision', type: 'protected' },
  ];

  const getEventColor = (type: string) => {
    switch (type) {
      case 'conflict':
        return 'error';
      case 'protected':
        return 'success';
      case 'module':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getEventIcon = (type: string) => {
    if (type === 'conflict') return <Warning sx={{ fontSize: 16 }} />;
    if (type === 'protected') return <Shield sx={{ fontSize: 16 }} />;
    return null;
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CalendarMonth color="primary" />
          <Typography variant="h6" color="primary">
            Integrated Schedule
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {events.map((event, index) => (
            <Box
              key={index}
              sx={{
                p: 1.5,
                borderRadius: 1,
                border: 1,
                borderColor: event.type === 'conflict' ? 'error.main' : event.type === 'protected' ? 'success.main' : 'divider',
                bgcolor: event.type === 'conflict' ? 'error.light' : event.type === 'protected' ? 'success.light' : 'action.hover',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500, minWidth: 80 }}>
                {event.time}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                {getEventIcon(event.type)}
                <Typography variant="body2">{event.title}</Typography>
              </Box>
            </Box>
          ))}
        </Box>
        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 2 }}>
          <Chip
            icon={<Warning sx={{ fontSize: 16 }} />}
            label="Conflict"
            size="small"
            variant="outlined"
            color="error"
          />
          <Chip
            icon={<Shield sx={{ fontSize: 16 }} />}
            label="Protected Time"
            size="small"
            variant="outlined"
            color="success"
          />
        </Box>
      </CardContent>
    </Card>
  );
}