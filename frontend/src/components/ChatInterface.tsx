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
        const response = await fetch(`${API_URL}/api/chat/history`, {
          headers: { Authorization: `Bearer ${session?.access_token}` },
        })
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
        headers: { Authorization: `Bearer ${session?.access_token}` },
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
    <Card
      sx={{
        height: '100%',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '20px',
        border: '1px solid #e1e7f2',
        bgcolor: '#ffffff',
        boxShadow: '0 20px 42px -32px rgba(43, 62, 103, 0.5)',
      }}
    >
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2.25, overflow: 'hidden' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.8 }}>
          <Chat sx={{ color: '#4f66ea', fontSize: 22 }} />
          <Typography sx={{ color: '#22304f', fontWeight: 700, fontSize: '1rem' }}>
            Chat with your AI Secretary
          </Typography>
        </Box>

        <Box
          sx={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 1.1,
            mb: 1.6,
            pr: 0.45,
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
                elevation={0}
                sx={{
                  maxWidth: '86%',
                  p: 1.2,
                  borderRadius: message.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  bgcolor: message.role === 'user' ? '#5a6df0' : '#f4f7ff',
                  color: message.role === 'user' ? '#ffffff' : '#2e3c5a',
                  border: message.role === 'user' ? 'none' : '1px solid #e1e8f5',
                }}
              >
                <Typography variant="body2" sx={{ lineHeight: 1.5 }}>
                  {message.content}
                </Typography>
              </Paper>
            </Box>
          ))}

          {isTyping && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <Paper elevation={0} sx={{ p: 1.2, borderRadius: '14px 14px 14px 4px', bgcolor: '#f4f7ff', border: '1px solid #e1e8f5' }}>
                <Typography variant="body2" sx={{ color: '#63718d' }}>
                  J².A.R.V.I.S is typing...
                </Typography>
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
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '12px',
                bgcolor: '#f9fbff',
                '& fieldset': { borderColor: '#d9e2f3' },
                '&:hover fieldset': { borderColor: '#c8d4ea' },
                '&.Mui-focused fieldset': { borderColor: '#7083f4' },
              },
            }}
          />

          <IconButton
            sx={{
              bgcolor: '#5a6df0',
              color: 'white',
              borderRadius: '12px',
              '&:hover': { bgcolor: '#4458dd' },
            }}
            onClick={handleSendAction}
          >
            <Send sx={{ fontSize: 20 }} />
          </IconButton>
        </Box>
      </CardContent>
    </Card>
  )
}
