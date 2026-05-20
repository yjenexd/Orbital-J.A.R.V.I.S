import { Card, CardContent, Typography, Box, TextField, IconButton, Paper } from '@mui/material';
import { Chat, Send } from '@mui/icons-material';
import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import type { ChatMessage } from '../types';

export function ChatInterface() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      text: 'Hello! I am your AI secretary. How can I assist you today?',
      sender: 'system',
      timestamp: Date.now(),
    },
    {
      id: '2', 
      text: 'Can you schedule a meeting with the marketing team tomorrow at 3 PM?',
      sender: 'user',
      timestamp: Date.now(),
    },
    {
      id: '3',
      text: 'Sure! I have scheduled a meeting with the marketing team for tomorrow at 3 PM.',
      sender: 'system',
      timestamp: Date.now(),
    },
    {
      id: '4',
      text: 'Great, thank you!',
      sender: 'user',
      timestamp: Date.now(),
    }
  ]);

  const messageEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' }); //checks if the ref is attached to a DOM element, and if so, scrolls it into view with a smooth animation
  }, [messages]); //watches the messages array, scrolls to bottom whenever a new message is added

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => { //read the input value and update the state
    setInputText(event.target.value);
  }

  const handleSendAction = () => { // add the user's message to the chat and clear the input

    if (!inputText.trim()) return; // prevent sending empty messages
    
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        id: Date.now().toString(),
        text: inputText,
        sender: 'user',
        timestamp: Date.now(),
      }
    ]);
    setInputText('');
  }

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => { //handle pressing Enter key to send message
    if (event.key === 'Enter') handleSendAction();
  }


  return (
    <Card sx={{ height: '600px', width: '400px', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 3 , overflow: 'hidden' }}>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2}}>
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
          <div ref={messageEndRef} /> {/* dummy div to scroll into view */}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            value={inputText}
            onChange={handleInputChange}
            placeholder="Type your command..."
            variant="outlined"
            onKeyPress ={handleKeyPress}
          />
          <IconButton color="primary" sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }} onClick={handleSendAction}>
            <Send />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  );
}