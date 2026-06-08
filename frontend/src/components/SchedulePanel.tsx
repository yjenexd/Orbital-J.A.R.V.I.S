import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { CalendarMonth, Warning, Shield } from '@mui/icons-material';
import { useEffect, useState } from 'react';
import { API_URL } from "../api";


interface ScheduleEvent {
  event_id: number;
  date: string;
  time: string;
  event: string;
  protected: boolean;
}

function detectConflicts(events: ScheduleEvent[]): Set<number> {
  const grouped = new Map<string, number[]>();

  for (const event of events) {
    const key = `${event.date}T${event.time}`;
    let ids = grouped.get(key);

    if (!ids) {
      ids = [];
      grouped.set(key, ids);
    }

    ids.push(event.event_id);
  }

  const conflicts = new Set<number>();
  for (const ids of grouped.values()) {
    if (ids.length > 1) ids.forEach(id => conflicts.add(id));
  }

  return conflicts;
}

export function SchedulePanel() {
  const [events, setEvents] = useState<ScheduleEvent[]>([]);

useEffect(() => {
    const fetchSchedule = () => {
      fetch(`${API_URL}/schedule`)
        .then(r => {
          if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
          return r.json();
        })
        .then(data => {
          // Add safety check before filtering
          if (!data.schedule || !Array.isArray(data.schedule)) {
            console.error("Invalid schedule data:", data);
            setEvents([]);
            return;
          }
          const today = '2026-05-19';
          const filtered = data.schedule.filter((e: ScheduleEvent) => e.date === today);
          setEvents(filtered);
        })
        .catch(err => {
          console.error("Failed to fetch schedule:", err);
          setEvents([]);
        });
    };

    fetchSchedule(); 
    const interval = setInterval(fetchSchedule, 5000); 
    return () => clearInterval(interval);
  }, []);

  const conflicts = detectConflicts(events);

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
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: 400, overflowY: 'auto' }}>
          {[...events]
            .sort((a, b) => `${a.date}T${a.time}`.localeCompare(`${b.date}T${b.time}`))
            .map((event) => (
              <Box
                key={event.event_id}
                sx={{
                  p: 1.5,
                  borderRadius: 1,
                  border: 1,
                  borderColor: conflicts.has(event.event_id) ? 'error.main' : event.protected ? 'success.main' : 'divider',
                  bgcolor: conflicts.has(event.event_id) ? 'error.light' : event.protected ? 'success.light' : 'action.hover',
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
          <Chip icon={<Warning sx={{ fontSize: 16 }} />} label="Conflict" size="small" variant="outlined" color="error" />
          <Chip icon={<Shield sx={{ fontSize: 16 }} />} label="Protected Time" size="small" variant="outlined" color="success" />
        </Box>
      </CardContent>
    </Card>
  );
}