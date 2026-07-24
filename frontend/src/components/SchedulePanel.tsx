import { Card, CardContent, Typography, Box } from '@mui/material'
import { CalendarMonth } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { fetchWithGroqKey } from '../api'
import { useAuth } from '../contexts/AuthContext'

interface ScheduleEvent {
  event_id: string
  date: string
  start_time: string
  end_time: string
  event: string
  protected: boolean
}

interface LayeredEvent extends ScheduleEvent {
  layer: number
  startPct: number
  widthPct: number
}

const HEADER_H = 24
const LAYER_H = 48

function normalize(time: string): string {
  return time.slice(0, 5)
}

export function toMinutes(time: string): number {
  const [h, m] = normalize(time).split(':').map(Number)
  return h * 60 + m
}

export function assignLayers(events: ScheduleEvent[]): LayeredEvent[] {
  const sorted = [...events].sort((a, b) =>
    normalize(a.start_time).localeCompare(normalize(b.start_time))
  )
  const layerEnds: number[] = []

  return sorted.map(event => {
    const startMins = toMinutes(event.start_time)
    let endMins = toMinutes(event.end_time)
    if (endMins <= startMins) endMins += 24 * 60

    const startPct = (startMins / 1440) * 100
    const widthPct = Math.max(((endMins - startMins) / 1440) * 100, 0.5)

    let layer = layerEnds.findIndex(end => end <= startMins)
    if (layer === -1) {
      layer = layerEnds.length
      layerEnds.push(endMins)
    } else {
      layerEnds[layer] = endMins
    }

    return { ...event, layer, startPct, widthPct }
  })
}

export function SchedulePanel() {
  const { session } = useAuth()
  const [events, setEvents] = useState<ScheduleEvent[]>([])
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    if (!session) return

    const fetchSchedule = async () => {
      try {
        const data = await fetchWithGroqKey<{ schedule: ScheduleEvent[] }>('/schedule', {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'X-Provider-Token': session.provider_token || '',
            'X-Provider-Refresh-Token': session.provider_refresh_token || '',
          },
        })
        if (!data.schedule || !Array.isArray(data.schedule)) { setEvents([]); return }
        const today = new Date().toLocaleDateString('en-CA')
        setEvents(data.schedule.filter((e: ScheduleEvent) => e.date === today))
      } catch {
        setEvents([])
      }
    }

    fetchSchedule()
    const pollInterval = setInterval(fetchSchedule, 60000)
    const clockInterval = setInterval(() => setNow(new Date()), 60000)
    const onFocus = () => fetchSchedule()
    const onUpdate = () => fetchSchedule()
    window.addEventListener('focus', onFocus)
    window.addEventListener('refreshSchedule', onUpdate)

    return () => {
      clearInterval(pollInterval)
      clearInterval(clockInterval)
      window.removeEventListener('focus', onFocus)
      window.removeEventListener('refreshSchedule', onUpdate)
    }
  }, [session])

  const layered = assignLayers(events)
  const numLayers = layered.reduce((max, e) => Math.max(max, e.layer + 1), 1)
  const timelineH = HEADER_H + numLayers * LAYER_H

  const nowPct = ((now.getHours() * 60 + now.getMinutes()) / 1440) * 100

  return (
    <Card
      sx={{
        borderRadius: '16px',
        border: '1px solid #e1e7f2',
        bgcolor: '#ffffff',
        boxShadow: '0 8px 24px -16px rgba(50, 72, 117, 0.35)',
        flexShrink: 0,
      }}
    >
      <CardContent sx={{ p: 2, pb: '12px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mb: 1 }}>
          <CalendarMonth sx={{ color: '#5b6ef0', fontSize: 18 }} />
          <Typography sx={{ color: '#22304f', fontWeight: 700, fontSize: '0.9rem' }}>
            Today's Schedule
          </Typography>
        </Box>

        <Box sx={{ position: 'relative', height: timelineH }}>
          {/* Hour gridlines + labels */}
          {Array.from({ length: 24 }).map((_, h) => (
            <Box
              key={h}
              sx={{
                position: 'absolute',
                left: `${(h / 24) * 100}%`,
                top: 0,
                height: '100%',
                borderLeft: '1px solid #edf0f7',
                pointerEvents: 'none',
              }}
            >
              <Typography
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 3,
                  color: '#b0bcd4',
                  fontSize: '0.6rem',
                  fontWeight: 600,
                  lineHeight: `${HEADER_H}px`,
                  whiteSpace: 'nowrap',
                }}
              >
                {String(h).padStart(2, '0')}:00
              </Typography>
            </Box>
          ))}

          {/* Divider below labels */}
          <Box
            sx={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: HEADER_H,
              height: '1px',
              bgcolor: '#e1e7f2',
              pointerEvents: 'none',
            }}
          />

          {/* Current time indicator */}
          <Box
            sx={{
              position: 'absolute',
              left: `${nowPct}%`,
              top: 0,
              height: '100%',
              width: '2px',
              bgcolor: '#eb5b6a',
              zIndex: 10,
              pointerEvents: 'none',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: HEADER_H - 4,
                left: '-3px',
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                bgcolor: '#eb5b6a',
              },
            }}
          />

          {/* Events */}
          {layered.map(event => (
            <Box
              key={event.event_id}
              title={`${event.event} · ${normalize(event.start_time)}–${normalize(event.end_time)}`}
              sx={{
                position: 'absolute',
                left: `${event.startPct}%`,
                width: `calc(${event.widthPct}% - 3px)`,
                top: HEADER_H + event.layer * LAYER_H + 4,
                height: LAYER_H - 8,
                borderRadius: '7px',
                bgcolor: event.protected ? '#e6f8ee' : '#edf1ff',
                border: `1px solid ${event.protected ? '#bde4cf' : '#ccd9fa'}`,
                px: 0.75,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                overflow: 'hidden',
                cursor: 'default',
                transition: 'filter 0.15s',
                '&:hover': { filter: 'brightness(0.94)' },
              }}
            >
              <Typography
                noWrap
                sx={{
                  color: event.protected ? '#2f9364' : '#5a69ce',
                  fontWeight: 700,
                  fontSize: '0.7rem',
                  lineHeight: 1.25,
                }}
              >
                {event.event}
              </Typography>
              <Typography
                noWrap
                sx={{
                  color: event.protected ? '#3d9f72' : '#7888d4',
                  fontSize: '0.6rem',
                  lineHeight: 1.25,
                }}
              >
                {normalize(event.start_time)}–{normalize(event.end_time)}
              </Typography>
            </Box>
          ))}

          {events.length === 0 && (
            <Typography
              sx={{
                position: 'absolute',
                top: HEADER_H + 14,
                left: 0,
                right: 0,
                textAlign: 'center',
                color: '#c4cedf',
                fontSize: '0.78rem',
              }}
            >
              No events scheduled today
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  )
}
