import { Card, CardContent, Typography, Box } from '@mui/material';
import { AutoAwesome } from '@mui/icons-material';

export function DailyBriefing() {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <AutoAwesome color="primary" />
          <Typography variant="h6" color="primary">
            Your Daily AI Briefing
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <Typography variant="body1">
            Good morning! You have <Typography component="span" sx={{ fontWeight: 500 }} color="primary">3 modules</Typography> today,
            a project meeting request from Jason at 2 PM (currently conflicts with your private tuition slot),
            <Typography component="span" sx={{ fontWeight: 500 }} color="primary"> 5 urgent emails</Typography> with summaries below,
            and <Typography component="span" sx={{ fontWeight: 500 }} color="primary">2 high-priority tasks</Typography>.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Note that your protected time for CS2040S revision is scheduled for 8 PM.
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}