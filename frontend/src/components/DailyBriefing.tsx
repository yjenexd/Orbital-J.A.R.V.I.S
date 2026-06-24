import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material'
import { AutoAwesome, EventAvailable } from '@mui/icons-material'
import { useState, useEffect } from 'react'
import { fetchWithGroqKey } from '../api'
import { useAuth } from '../contexts/AuthContext'

interface BriefingResponse {
  briefing: string
  has_events: boolean
}

function renderBriefingText(text: string) {
  const emphasisPattern = /(\b\d+\s+(?:modules?|urgent emails?|high-priority tasks?)\b|\b\d{1,2}\s?(?:AM|PM)\b)/gi
  const segments = text.split(emphasisPattern)

  return segments.map((segment, index) => {
    if (segment.match(emphasisPattern)) {
      return (
        <Box
          key={`emphasis-${index}`}
          component="span"
          sx={{
            display: 'inline-block',
            px: 0.65,
            py: 0.14,
            mx: 0.16,
            bgcolor: 'rgba(214, 224, 255, 0.24)',
            border: '1px solid rgba(231, 237, 255, 0.28)',
            color: '#f6f8ff',
            fontWeight: 700,
          }}
        >
          {segment}
        </Box>
      )
    }

    return (
      <Box key={`text-${index}`} component="span" sx={{ color: '#edf1ff' }}>
        {segment}
      </Box>
    )
  })
}

export function DailyBriefing() {
  const { session } = useAuth()
  const [briefing, setBriefing] = useState<string | null>(null)
  const [isLoadingBriefing, setIsLoadingBriefing] = useState<boolean>(true)
  const [hasEvents, setHasEvents] = useState<boolean>(false)

  useEffect(() => {
    if (!session) return
    const fetchBriefing: () => Promise<void> = async () => {
      try {
        const data = await fetchWithGroqKey<BriefingResponse>('/api/briefing')
        setBriefing(data.briefing)
        setHasEvents(data.has_events)
      } catch (error: string | any) {
        console.error(error)
        const errorMessage =
          error.message === 'API_KEY_MISSING'
            ? 'System offline: Please save your Groq API key in the Profile tab first.'
            : 'System error: Failed to connect to intelligence backend.'
        setBriefing(errorMessage)
      } finally {
        setIsLoadingBriefing(false)
      }
    }

    fetchBriefing()
  }, [session])

  const todayLabel = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  }).format(new Date())

  return (
    <Card
      sx={{
        borderRadius: '20px',
        border: '1px solid #d5def4',
        background: 'linear-gradient(106deg, #4b6fe8 0%, #647def 58%, #9a80ec 100%)',
        color: '#f7f9ff',
        boxShadow: '0 20px 38px -28px rgba(74, 93, 195, 0.85)',
      }}
    >
      <CardContent sx={{ px: { xs: 2, sm: 2.4 }, py: { xs: 1.8, sm: 2.1 }, pb: '18px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, mb: 1.05 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.05 }}>
            <Box
              sx={{
                width: 28,
                height: 28,
                borderRadius: '9px',
                display: 'grid',
                placeItems: 'center',
              }}
            >
              <AutoAwesome sx={{ fontSize: 15, color: '#f4f7ff' }} />
            </Box>
            <Typography sx={{ fontWeight: 800, fontSize: { xs: '1.18rem', sm: '1.28rem' }, letterSpacing: '-0.01em', color: '#f7f9ff' }}>
              Your Daily AI Briefing
            </Typography>
          </Box>

          <Typography
            sx={{
              fontSize: '0.76rem',
              fontWeight: 700,
              color: '#eef3ff',
              opacity: 0.92,
            }}
          >
            {todayLabel}
          </Typography>
        </Box>

        {isLoadingBriefing ? (
          <Box>
            <Skeleton animation="wave" sx={{ bgcolor: 'rgba(238,242,255,0.32)', mb: 0.7, borderRadius: 999 }} />
            <Skeleton animation="wave" sx={{ bgcolor: 'rgba(238,242,255,0.32)', width: '84%', borderRadius: 999 }} />
          </Box>
        ) : !hasEvents ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.8, opacity: 0.95 }}>
            <EventAvailable sx={{ fontSize: 18, color: '#f1f5ff' }} />
            <Typography variant="body2" sx={{ fontStyle: 'italic', color: '#edf1ff' }}>
              {briefing}
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" sx={{ lineHeight: 1.68, fontSize: '0.96rem', fontWeight: 600, color: '#edf1ff' }}>
            {briefing ? renderBriefingText(briefing) : null}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
