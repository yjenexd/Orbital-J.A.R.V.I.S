import { Card, CardContent, Typography, Box } from '@mui/material';
import { AutoAwesome } from '@mui/icons-material';
import {useState, useEffect} from 'react';


export function DailyBriefing() {

  const [briefing, setBriefing] = useState<string | null>(null);
  const [isLoadingBriefing, setIsLoadingBriefing] = useState(true);

  //fetch the summary on initialization
  useEffect(() => {
    const fetchBriefing: () => Promise<void> = async () =>  {
      try {
        const response = await fetch('http://localhost:8000/api/briefing')
        if (!response.ok) throw new Error('Failed to fetch briefing');

        const data: { briefing: string } = await response.json();
        setBriefing(data.briefing);
      } catch (error) {
        console.error(error);
        setBriefing("Unable to load daily briefing. Core systems offline.");
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
        <Typography variant="body2">
          {isLoadingBriefing ? "Initializing cognitive summary..." : briefing}
        </Typography>
      </CardContent>
    </Card>
  );
}