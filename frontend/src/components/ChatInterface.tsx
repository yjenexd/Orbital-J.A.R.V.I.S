import { Card, CardContent, Typography, Box, TextField, IconButton, Paper } from '@mui/material';
import { Chat, Send } from '@mui/icons-material';
import { useState } from 'react';

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

export function ChatInterface() {
  const [input, setInput] = useState('');
  const [messages] = useState<Message[]>([
    {
      sender: 'user',
      text: 'Push all my math tuition classes back by an hour tomorrow so I can study for my CS2040S exam',
    },
    {
      sender: 'ai',
      text: 'I\'ve rescheduled all your MA1521 tuition sessions for tomorrow, moving them from 2:00 PM to 3:00 PM. This clears your schedule from 2:00-3:00 PM for CS2040S exam preparation. Would you like me to send notifications to your tuition instructor?',
    },
    {
      sender: 'user',
      text: 'Yes, please send the notification.',
    },
    {
      sender: 'ai',
      text: 'Done! Notification sent to your tuition instructor. I\'ve also blocked the 2:00-3:00 PM slot as "CS2040S Study Time" to prevent any scheduling conflicts.',
    },
  ]);

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Chat color="primary" />
          <Typography variant="h6" color="primary">
            Chat with your AI Secretary
          </Typography>
        </Box>
        <Box
          sx={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 1.5,
            mb: 2,
          }}
        >
          {messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <Paper
                elevation={1}
                sx={{
                  maxWidth: '80%',
                  p: 1.5,
                  bgcolor: message.sender === 'user' ? 'primary.main' : 'grey.100',
                  color: message.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                }}
              >
                <Typography variant="body2">{message.text}</Typography>
              </Paper>
            </Box>
          ))}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your command..."
            variant="outlined"
          />
          <IconButton color="primary" sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }}>
            <Send />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  );
}