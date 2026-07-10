import { Card, CardContent, Typography, Box, Chip } from '@mui/material'
import { CalendarMonth, Warning, Shield } from '@mui/icons-material'
import { useEffect, useState } from 'react'
import { fetchWithGroqKey } from '../api'
import { useAuth } from '../contexts/AuthContext'



interface ScheduleEvent {
  event_id: string
  date: string
  time: string
  event: string
  protected: boolean
}

type EventTheme = {
  itemBg: string
  itemBorder: string
  itemAccent: string
  titleColor: string
  timeColor: string
}

function detectConflicts(events: ScheduleEvent[]): Set<string> {
  const grouped = new Map<string, string[]>()

  for (const event of events) {
    const key = `${event.date}T${event.time}`
    let ids = grouped.get(key)

    if (!ids) {
      ids = []
      grouped.set(key, ids)
    }

    ids.push(event.event_id)
  }

  const conflicts = new Set<string>()
  for (const ids of grouped.values()) {
    if (ids.length > 1) ids.forEach((id) => conflicts.add(id))
  }

  return conflicts
}

function getEventTheme(isConflict: boolean, isProtected: boolean): EventTheme {
  if (isConflict) {
    return {
      itemBg: '#fff4f5',
      itemBorder: '#f1c8ce',
      itemAccent: '#eb5b6a',
      titleColor: '#c84a59',
      timeColor: '#e06a77',
    }
  }

  if (isProtected) {
    return {
      itemBg: '#e6f8ee',
      itemBorder: '#bde4cf',
      itemAccent: '#20b56f',
      titleColor: '#2f9364',
      timeColor: '#3d9f72',
    }
  }

  return {
    itemBg: '#edf1ff',
    itemBorder: '#ccd9fa',
    itemAccent: '#5d6ff1',
    titleColor: '#5a69ce',
    timeColor: '#7888d4',
  }
}

function formatTimeRange(time: string): string {
  const [hourRaw, minuteRaw] = time.split(':')
  const hour = Number(hourRaw)
  const minute = Number(minuteRaw)

  if (Number.isNaN(hour) || Number.isNaN(minute)) return time

  const start = new Date()
  start.setHours(hour, minute, 0, 0)

  const end = new Date(start)
  end.setHours(end.getHours() + 1)

  const format = (date: Date) =>
    `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`

  return `${format(start)} - ${format(end)}`
}

export function SchedulePanel() {
  const { session } = useAuth()
  const [events, setEvents] = useState<ScheduleEvent[]>([])

  useEffect(() => {
    if (!session) return

    const fetchSchedule = async () => {
      try {
        const data = await fetchWithGroqKey<{ schedule: ScheduleEvent[] }>('/schedule', {
          headers: { 
            Authorization: `Bearer ${session.access_token}`,
            // Pass the Google credentials to your FastAPI backend
            'X-Provider-Token': session.provider_token || '',
            'X-Provider-Refresh-Token': session.provider_refresh_token || ''
          },
        })

        if (!data.schedule || !Array.isArray(data.schedule)) {
          console.error('Invalid schedule data:', data)
          setEvents([])
          return
        }

        const today = new Date().toLocaleDateString('en-CA')
        const filtered = data.schedule.filter((e: ScheduleEvent) => e.date === today)
        setEvents(filtered)
      } catch (err) {
        console.error('Failed to fetch schedule:', err)
        setEvents([])
      }
    }
    
    fetchSchedule()
    const interval = setInterval(fetchSchedule, 60000)

    //Refetch when the user tabs back into the app
    const handleFocus = () => fetchSchedule()
    window.addEventListener('focus', handleFocus)

    // Refetch when our app manually triggers an update (e.g., from the chat)
    const handleCustomUpdate = () => fetchSchedule()
    window.addEventListener('refreshSchedule', handleCustomUpdate)

    // Cleanup all listeners on unmount
    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('refreshSchedule', handleCustomUpdate)
    }
  }, [session])

  const conflicts = detectConflicts(events)

  return (
    <Card
      sx={{
        borderRadius: '20px',
        border: '1px solid #e1e7f2',
        bgcolor: '#ffffff',
        boxShadow: '0 18px 38px -30px rgba(50, 72, 117, 0.45)',
      }}
    >
      <CardContent sx={{ p: 2.25 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CalendarMonth sx={{ color: '#5b6ef0' }} />
            <Typography sx={{ color: '#22304f', fontWeight: 700, fontSize: { xs: '1.18rem', sm: '1.3rem' } }}>
              Today's Schedule
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.1 }}>
            <Chip icon={<Warning sx={{ fontSize: 14 }} />} label="Conflict" size="small" sx={{ bgcolor: '#fff4f5', color: '#c24b59', border: '1px solid #f1c9ce' }} />
            <Chip icon={<Shield sx={{ fontSize: 14 }} />} label="Protected" size="small" sx={{ bgcolor: '#edf9f2', color: '#2f9364', border: '1px solid #cae9d8' }} />
          </Box>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: 362, overflowY: 'auto', pr: 0.4 }}>
          {[...events]
            .sort((a, b) => `${a.date}T${a.time}`.localeCompare(`${b.date}T${b.time}`))
            .map((event) => {
              const isConflict = conflicts.has(event.event_id)
              const theme = getEventTheme(isConflict, event.protected)

              return (
                <Box
                  key={event.event_id}
                  sx={{
                    p: 1.15,
                    borderRadius: '11px',
                    border: `1px solid ${theme.itemBorder}`,
                    bgcolor: theme.itemBg,
                    display: 'flex',
                    alignItems: 'stretch',
                    gap: 1,
                  }}
                >
                  <Box sx={{ width: 4, borderRadius: 99, bgcolor: theme.itemAccent, flexShrink: 0 }} />

                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ color: theme.titleColor, fontWeight: 700, lineHeight: 1.35, fontSize: '0.92rem' }}>
                      {event.event}
                    </Typography>
                    <Typography variant="caption" sx={{ color: theme.timeColor, fontWeight: 700, fontSize: '0.75rem' }}>
                      {formatTimeRange(event.time)}
                    </Typography>
                  </Box>

                  {isConflict && <Warning sx={{ color: '#e65062', fontSize: 17, mt: 0.3 }} />}
                  {!isConflict && event.protected && <Shield sx={{ color: '#27a868', fontSize: 17, mt: 0.3 }} />}
                </Box>
              )
            })}
        </Box>
      </CardContent>
    </Card>
  )
}
