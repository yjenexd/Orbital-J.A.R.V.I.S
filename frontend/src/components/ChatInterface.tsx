import { Card, CardContent, Typography, Box, TextField, IconButton, Paper } from '@mui/material'
import { Chat, Send } from '@mui/icons-material'
import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { API_URL, fetchWithGroqKey } from '../api'
import { useAuth } from '../contexts/AuthContext'
import type { ChatMessage } from '../types'

export function ChatInterface() {
  const { session } = useAuth()
  const [inputText, setInputText] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)

  const messageEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  useEffect(() => {
    const userId = session?.user.id
    if (!userId) return

    const loadChatHistory = async () => {
      try {
        const response = await fetch(`${API_URL}/api/chat/history?user_id=${encodeURIComponent(userId)}`)
        if (!response.ok) {
          throw new Error('Failed to fetch history')
        }

        const data = await response.json()
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages)
        }
      } catch (error) {
        console.error('Error loading chat history:', error)
      }
    }

    void loadChatHistory()
  }, [session])

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    setInputText(event.target.value)
  }

  const handleSendAction = async () => {
    const userId = session?.user.id
    const trimmedInput = inputText.trim()

    if (!trimmedInput || isTyping || !userId) return

    const userMessage: ChatMessage = {
      message_id: Date.now(),
      user_id: userId,
      role: 'user',
      content: trimmedInput,
      created_at: Date.now().toString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputText('')
    setIsTyping(true)

    try {
      const data = await fetchWithGroqKey<{ reply: string }>('/chat', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, message: trimmedInput }),
      })

      setMessages((prev) => [
        ...prev,
        {
          message_id: Date.now(),
          user_id: userId,
          content: data.reply,
          role: 'system',
          created_at: Date.now().toString(),
        },
      ])
    } catch (error: string | any) {
      console.error('Error communicating with the backend:', error)

      const errorMessage =
        error.message === 'API_KEY_MISSING'
          ? '⚠️ System offline: Please save your Groq API key in the Profile tab first.'
          : '⚠️ System error: Failed to connect to intelligence backend.'

      setMessages((prev) => [
        ...prev,
        {
          message_id: Date.now(),
          user_id: userId,
          content: errorMessage,
          role: 'system',
          created_at: Date.now().toString(),
        },
      ])
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') handleSendAction()
  }

  return (
    <Card sx={{ height: '600px', width: '400px', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 3, overflow: 'hidden' }}>
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
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <Paper
                elevation={1}
                sx={{
                  maxWidth: '80%',
                  p: 1.5,
                  bgcolor: message.role === 'user' ? 'primary.main' : 'grey.100',
                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                }}
              >
                <Typography variant="body2">{message.content}</Typography>
              </Paper>
            </Box>
          ))}

          {isTyping && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <Paper elevation={1}>
                <Typography variant="body2">J².A.R.V.I.S is typing...</Typography>
              </Paper>
            </Box>
          )}
          <div ref={messageEndRef} />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            size="small"
            value={inputText}
            onChange={handleInputChange}
            placeholder="Type your command..."
            variant="outlined"
            onKeyPress={handleKeyPress}
            disabled={isTyping}
            multiline
            maxRows={4}
          />

          <IconButton
            color="primary"
            sx={{ bgcolor: 'primary.main', color: 'white', '&:hover': { bgcolor: 'primary.dark' } }}
            onClick={handleSendAction}
          >
            <Send />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  )
}
