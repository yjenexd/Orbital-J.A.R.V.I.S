import { useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { Box, Typography } from '@mui/material';
import type { EventClickArg } from '@fullcalendar/core';
import { API_URL } from "../api";


interface ScheduleEvent {
  event_id: string;
  date: string;
  time: string;
  event: string;
  protected: boolean;
}

export function CalendarView() {
  const [events, setEvents] = useState<any[]>([]);

  const handleDatesSet = (dateInfo: any) => {
    const timeMin = new Date(dateInfo.start).toISOString();
    const timeMax = new Date(dateInfo.end).toISOString();
    
    fetch(`${API_URL}/calendar?time_min=${timeMin}&time_max=${timeMax}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (!data.schedule || !Array.isArray(data.schedule)) {
          console.error("Invalid data format received:", data);
          setEvents([]); 
          return;
        }

        const formatted = data.schedule.map((e: ScheduleEvent) => {
          const start = `${e.date}T${e.time}`;
          const endDate = new Date(start);
          endDate.setHours(endDate.getHours() + 1);
          return {
            id: String(e.event_id),
            title: e.event,
            start,
            end: endDate.toISOString(),
            backgroundColor: e.protected ? '#2e7d32' : '#1976d2',
            borderColor: e.protected ? '#2e7d32' : '#1976d2',
          };
        });
        setEvents(formatted);
      })
      .catch(error => {
        console.error("Failed to fetch calendar events:", error);
        setEvents([]);
      });
  };

  return (
    <Box sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 1, height: '100%' }}>
      <Typography variant="h6" color="primary" sx={{ mb: 2 }}>
        Calendar
      </Typography>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        initialDate="2026-05-19"
        now="2026-05-19"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        }}
        events={events}
        datesSet={handleDatesSet}
        dayMaxEvents={3}
        height="auto"
        nowIndicator={true}
        eventTimeFormat={{
          hour: '2-digit',
          minute: '2-digit',
          hour12: true
        }}
        eventClick={(info: EventClickArg) => alert(info.event.title)}
      />
    </Box>
  );
}