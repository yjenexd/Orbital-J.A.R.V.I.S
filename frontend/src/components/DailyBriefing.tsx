import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material';
import { AutoAwesome, EventAvailable } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { fetchWithGroqKey } from "../api";


interface BriefingResponse {
  briefing: string;
  has_events: boolean;
}

export function DailyBriefing() {
  const [briefing, setBriefing] = useState<string | null>(null);
  const [isLoadingBriefing, setIsLoadingBriefing] = useState<boolean>(true);
  const [hasEvents, setHasEvents] = useState<boolean>(false);

  // Fetch the summary on initialization
  useEffect(() => {
    const fetchBriefing: () => Promise<void> = async () => {
      try {
        const data = await fetchWithGroqKey<BriefingResponse>('/api/briefing');
          setBriefing(data.briefing);
          setHasEvents(data.has_events);
      } catch (error: string | any) {
          console.error(error);
          const errorMessage = error.message === 'API_KEY_MISSING' 
            ? "⚠️ System offline: Please save your Groq API key in the Profile tab first."
            : "⚠️ System error: Failed to connect to intelligence backend.";
          setBriefing(errorMessage);
      } finally {
          setIsLoadingBriefing(false);
      }
    };

    fetchBriefing();
  }, []);

  return (
    <Card sx={{ mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText', borderRadius: 2 }}>
      <CardContent sx={{ pb: '16px !important' }}> {/* Keeps padding tight */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <AutoAwesome sx={{ fontSize: 20 }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
            Day at a Glance
          </Typography>
        </Box>
        
        {isLoadingBriefing ? (
          <Box>
            <Skeleton animation="wave" sx={{ bgcolor: 'rgba(255,255,255,0.4)', mb: 0.5 }} />
            <Skeleton animation="wave" sx={{ bgcolor: 'rgba(255,255,255,0.4)', width: '80%' }} />
          </Box>
        ) : !hasEvents ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1, opacity: 0.9 }}>
            <EventAvailable sx={{ fontSize: 18 }} />
            <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
              {briefing}
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2">
            {briefing}
          </Typography>
        )}
        
      </CardContent>
    </Card>
  );
}