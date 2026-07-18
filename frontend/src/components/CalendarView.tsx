import { useState } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { Box, Typography } from '@mui/material'
import type { EventClickArg } from '@fullcalendar/core'
import { API_URL } from '../api'
import { useAuth } from '../contexts/AuthContext'

interface ScheduleEvent {
  event_id: string
  date: string
  start_time: string
  end_date: string
  end_time: string
  event: string
  protected: boolean
}

export function CalendarView() {
  const { session } = useAuth()
  const [events, setEvents] = useState<any[]>([])

  const handleDatesSet = (dateInfo: any) => {
    const timeMin = new Date(dateInfo.start).toISOString()
    const timeMax = new Date(dateInfo.end).toISOString()

    fetch(`${API_URL}/calendar?time_min=${timeMin}&time_max=${timeMax}`, {
      headers: { Authorization: `Bearer ${session?.access_token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`)
        return r.json()
      })
      .then((data) => {
        if (!data.schedule || !Array.isArray(data.schedule)) {
          console.error('Invalid data format received:', data)
          setEvents([])
          return
        }

        const formatted = (data.schedule as ScheduleEvent[])
          .map((e: ScheduleEvent) => {
            if (!e.date) {
              console.warn('Skipping calendar event with no date:', e)
              return null
            }

            const color = e.protected ? '#5fb98c' : '#63a6eb'

            // An event with no time (e.g. a deadline) is a valid all-day event.
            // Render it as such instead of dropping it or forcing it to midnight.
            if (!e.time) {
              return {
                id: String(e.event_id),
                title: e.event,
                start: e.date,
                allDay: true,
                backgroundColor: color,
                borderColor: color,
              }
            }

            const start = `${e.date}T${e.time}`
            const startDate = new Date(start)
            if (Number.isNaN(startDate.getTime())) {
              console.warn('Skipping calendar event with invalid date/time:', e)
              return null
            }
            const endDate = new Date(startDate)
            endDate.setHours(endDate.getHours() + 1)
            return {
              id: String(e.event_id),
              title: e.event,
              start,
              end: endDate.toISOString(),
              backgroundColor: color,
              borderColor: color,
            }
          })
          .filter((ev) => ev !== null)
        setEvents(formatted)
      })
      .catch((error) => {
        console.error('Failed to fetch calendar events:', error)
        setEvents([])
      })
  }

  return (
    <Box
      sx={{
        p: { xs: 1.4, sm: 1.8 },
        bgcolor: '#ffffff',
        borderRadius: '20px',
        border: '1px solid #e1e7f2',
        height: '100%',
        boxShadow: '0 20px 42px -32px rgba(43, 62, 103, 0.5)',
      }}
    >
      <Typography sx={{ mb: 1.4, fontWeight: 700, fontSize: '1.06rem', color: '#243251' }}>
        Calendar
      </Typography>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
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
          hour12: true,
        }}
        eventClick={(info: EventClickArg) => alert(info.event.title)}
      />
    </Box>
  )
}
