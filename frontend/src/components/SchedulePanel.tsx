import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { CalendarMonth, Warning, Shield } from '@mui/icons-material';

interface ScheduleEvent {
  event_id: number;
  date: string;
  time: string;
  event: string;
  protected: boolean
  user_id: number;
}
function detectConflicts(events: ScheduleEvent[]): Set<number> {
  const grouped = new Map<string, number[]>();

  for (const event of events) {
    // FIX: Combine the date and time strings to create a unique, valid key
    const key = `${event.date}T${event.time}`; 
    
    grouped.set(key, [...(grouped.get(key) ?? []), event.event_id]);
  }

  const conflicts = new Set<number>();
  for (const ids of grouped.values()) {
    if (ids.length > 1) ids.forEach(id => conflicts.add(id));
  }

  return conflicts;
}

export function SchedulePanel() {
  const events: ScheduleEvent[] = [
	{
		"event_id": 1,
		"date": "2026-05-19",
		"time": "09:00:00",
		"event": "CS2040S - Data Structures",
		"protected": false,
		"user_id": 1
	},
	{
		"event_id": 2,
		"date": "2026-05-19",
		"time": "11:00:00",
		"event": "CS2030S - Programming Methodology",
		"protected": false,
		"user_id": 1
	},
	{
		"event_id": 3,
		"date": "2026-05-19",
		"time": "14:00:00",
		"event": "Project Meeting with Jason",
		"protected": false,
		"user_id": 1
	},
	{
		"event_id": 4,
		"date": "2026-05-19",
		"time": "14:00:00",
		"event": "Private Tuition Slot",
		"protected": false,
		"user_id": 1
	},
	{
		"event_id": 5,
		"date": "2026-05-19",
		"time": "16:00:00",
		"event": "MA1521 - Calculus",
		"protected": false,
		"user_id": 1
	},
	{
		"event_id": 6,
		"date": "2026-05-19",
		"time": "20:00:00",
		"event": "CS2040S Revision",
		"protected": true,
		"user_id": 1
	},
	{
		"event_id": 7,
		"date": "2026-05-19",
		"time": "16:00:00",
		"event": "Floorball practice",
		"protected": false,
		"user_id": 1
	},
	{
		"event_id": 8,
		"date": "2026-05-19",
		"time": "11:00:00",
		"event": "IS1108 Consultation",
		"protected": false,
		"user_id": 1
	}
];
  const conflicts = detectConflicts(events);

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

  const getEventIcon = (eventId: number, isProtected: boolean) => {
    if (conflicts.has(eventId)) return <Warning sx={{ fontSize: 16 }} />;
    if (isProtected) return <Shield sx={{ fontSize: 16 }} />;
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
                borderColor: conflicts.has(event.event_id) ? 'error.main' : event.protected === true ? 'success.main' : 'divider',
                bgcolor: conflicts.has(event.event_id) ? 'error.light' : event.protected === true ? 'success.light' : 'action.hover',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500, minWidth: 80 }}>
                {event.time}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                {getEventIcon(event.event_id, event.protected)}
                <Typography variant="body2">{event.event}</Typography>
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