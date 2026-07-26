import { useCallback, useEffect, useRef, useState } from 'react'
import FullCalendar from '@fullcalendar/react'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { Box, Typography } from '@mui/material'
import type { DatesSetArg, EventClickArg, EventInput } from '@fullcalendar/core'
import { API_URL } from '../api'
import { useAuth } from '../contexts/AuthContext'

interface ScheduleEvent {
  event_id: string
  date: string
  start_time: string
  end_date: string
  end_time: string
  event: string
}

// Coalesce the bursts of datesSet callbacks FullCalendar fires while the user
// clicks through views/weeks, so we issue one request for where they land.
const FETCH_DEBOUNCE_MS = 200

export function CalendarView() {
  const { session } = useAuth()
  const [events, setEvents] = useState<EventInput[]>([])

  const accessToken = session?.access_token
  // Mutated inside handlers/effects only (never during render) so we can cancel
  // stale work and skip duplicate range fetches.
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const lastRangeRef = useRef<string | null>(null)

  const fetchRange = useCallback((timeMin: string, timeMax: string) => {
    const rangeKey = `${timeMin}|${timeMax}`
    // The same visible range can be reported repeatedly (re-renders, view toggles
    // that map to identical bounds); skip the redundant round-trip.
    if (rangeKey === lastRangeRef.current) return
    lastRangeRef.current = rangeKey

    // Cancel any request still in flight so a slow earlier response can't clobber
    // the newest view.
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    fetch(`${API_URL}/calendar?time_min=${timeMin}&time_max=${timeMax}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal: controller.signal,
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

            const color = '#63a6eb'

            // An event with no time (e.g. a deadline) is a valid all-day event.
            // Render it as such instead of dropping it or forcing it to midnight.
            if (!e.start_time) {
              return {
                id: String(e.event_id),
                title: e.event,
                start: e.date,
                allDay: true,
                backgroundColor: color,
                borderColor: color,
              }
            }

            const start = `${e.date}T${e.start_time}`
            const startDate = new Date(start)
            if (Number.isNaN(startDate.getTime())) {
              console.warn('Skipping calendar event with invalid date/time:', e)
              return null
            }
            const end = `${e.end_date}T${e.end_time}`
            return {
              id: String(e.event_id),
              title: e.event,
              start,
              end,
              backgroundColor: color,
              borderColor: color,
            }
          })
          .filter((ev) => ev !== null)
        setEvents(formatted)
      })
      .catch((error) => {
        if (error?.name === 'AbortError') return
        console.error('Failed to fetch calendar events:', error)
        setEvents([])
      })
  }, [accessToken])

  const handleDatesSet = useCallback(
    (dateInfo: DatesSetArg) => {
      const timeMin = new Date(dateInfo.start).toISOString()
      const timeMax = new Date(dateInfo.end).toISOString()

      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => fetchRange(timeMin, timeMax), FETCH_DEBOUNCE_MS)
    },
    [fetchRange]
  )

  // Tidy up the pending timer and any in-flight request on unmount.
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      abortRef.current?.abort()
    }
  }, [])

  return (
    <Box
      sx={{
        p: { xs: 1.4, sm: 1.8 },
        bgcolor: '#ffffff',
        borderRadius: '20px',
        border: '1px solid #e1e7f2',
        height: '100%',
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 42px -32px rgba(43, 62, 103, 0.5)',
      }}
    >
      <Typography sx={{ mb: 1.4, fontWeight: 700, fontSize: '1.06rem', color: '#243251', flexShrink: 0 }}>
        Calendar
      </Typography>
      {/* Constrain the calendar so its time grid scrolls internally instead of
          stretching the whole page — smoother, and the day headers stay pinned. */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
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
          height="100%"
          expandRows={true}
          stickyHeaderDates={true}
          scrollTime="08:00:00"
          nowIndicator={true}
          eventTimeFormat={{
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
          }}
          eventClick={(info: EventClickArg) => alert(info.event.title)}
        />
      </Box>
    </Box>
  )
}
