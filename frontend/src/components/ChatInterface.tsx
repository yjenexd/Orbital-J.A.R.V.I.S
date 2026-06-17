import { Card, CardContent, Typography, Box, TextField, IconButton, Paper } from '@mui/material';
import { Chat, Send } from '@mui/icons-material';
import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import type { ChatMessage } from '../types';
import { API_URL } from "../api";
import { useAuth } from '../contexts/AuthContext';
/**
 * A fixed-size conversational UI panel that renders a scrollable message chain.
 * Currently operates with localized state to track user inputs and mock AI replies.
 * 
 * @component
 * @example
 * // Usage in a parent layout:
 * return (
 *   <Box sx={{ p: 2 }}>
 *     <ChatInterface />
 *   </Box>
 * )
 */

export function ChatInterface() {
  const { session } = useAuth();
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]); //local state to hold the conversation history, initialized as an empty array
  const [isTyping, setIsTyping] = useState(false); //state to track if the AI is currently "typing" a response, used to disable input and show loading indicators if needed

  const messageEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' }); //checks if the ref is attached to a DOM element, and if so, scrolls it into view with a smooth animation
  }, [messages, isTyping]); //watches the messages array, scrolls to bottom whenever a new message is added

  useEffect(() => {
    if (!session) return;
    const loadChatHistory = async() => {
      try{
        const response = await fetch(`${API_URL}/api/chat/history`, {
          headers: { 'Authorization': `Bearer ${session.access_token}` },
        });
        if(!response.ok) {
          throw new Error('Failed to fetch history');
        }

        const data = await response.json()

        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
        }
      } catch (error) {
        console.error("Error loading chat history:", error);
      }
    };

    loadChatHistory();
  }, [session]);
  

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => { //read the input value and update the state
    setInputText(event.target.value);
  }

  const handleSendAction = async () => { //pairs with await, simulates sending the user input to the backend and receiving a response
    const trimmedInput = inputText.trim(); //clean the string

    if(!trimmedInput || isTyping) return; 

    //1. Add users message to the UI
    const userMessage: ChatMessage = {
      message_id: Date.now(), //using timestamp as a simple unique ID for messages
      user_id: session?.user.id ?? '',
      role: 'user',
      content: trimmedInput,
      created_at: Date.now().toString(),
    };

    setMessages((prev) => [...prev, userMessage]); //append the new message to the existing arrray of Messages
    setInputText(''); 

    //2. turn on the loading indicator while waiting for the response
    setIsTyping(true); 
    try {
      //3. Send data to the Python backend
      const response = await fetch(`${API_URL}/chat`, {  //Documentation: MDN
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify({ message: trimmedInput }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.statusText}`);
      }
      const data = await response.json();

      //4. Append AI response to UI
      setMessages((prev) => [
        ...prev,
        {
          message_id: Date.now(),
          user_id: session?.user.id ?? '',
          content: data.reply,
          role: 'system',
          created_at: Date.now().toString(),
        }
      ]);
      } catch (error) {
        console.error("Error communicating with the backend:", error);
      } finally {
        setIsTyping(false);
      }
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
        
        {/* THIS IS THE SCROLLABLE CHA HISTORY */}
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
          {/* creates a bubble for every saved message */}
          {messages.map((message, index) => (
            //invisible bubble that pushes bubble to left or right
            <Box
              key={index}
              sx={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {/* The actual colored message bubble with a shadow */}
              <Paper
                elevation={1}
                sx={{
                  maxWidth: '80%',
                  p: 1.5,
                  bgcolor: message.role === 'user' ? 'primary.main' : 'grey.100',
                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                }}
              >
                {/* The text inside the bubble */}
                <Typography variant="body2">{message.content}</Typography>
              </Paper>
            </Box>
          ))}

          {/* THE LOADING BUBBLE: Only shows up when waiting for the backend */}
          {isTyping && (
            <Box sx = {{display: 'flex', justifyContent: 'flex-start' }}>
              <Paper elevation={1} sx={{}}>
                 <Typography variant = "body2">
                  J².A.R.V.I.S is typing...
                 </Typography>
              </Paper>
            </Box>
          )}
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
            disabled = {isTyping} //locks field while AI is thinking
            multiline
            maxRows = {4} //stop growing after 4 lines, starts scrolling within the text field
          />

          {/* paper airplane icon*/}
          <IconButton color="primary" sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }} onClick={handleSendAction}>
            <Send />
          </IconButton>
        </Box>

      </CardContent>
    </Card>
  );
}