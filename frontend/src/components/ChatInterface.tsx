import { Card, CardContent, Typography, Box, TextField, IconButton, Paper } from '@mui/material'
import { Chat, Send } from '@mui/icons-material'
import { useEffect, useLayoutEffect, useRef, useState, type ChangeEvent, type UIEvent } from 'react'
import { API_URL, fetchWithGroqKey } from '../api'
import { useAuth } from '../contexts/AuthContext'
import type { ChatMessage } from '../types'

// How many messages to render at once, and how many more to reveal each time the
// user scrolls to the top. Keeps the DOM small on long histories.
const PAGE_SIZE = 30
// Treat the view as "at the bottom" within this many px, so auto-scroll only
// fires when the user is actually following the conversation.
const NEAR_BOTTOM_PX = 120
// Reveal older messages once the user scrolls within this many px of the top.
const TOP_LOAD_PX = 60

export function ChatInterface() {
  const { session } = useAuth()
  const [inputText, setInputText] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  const listRef = useRef<HTMLDivElement>(null)
  const messageEndRef = useRef<HTMLDivElement>(null)
  // Kept in refs so the scroll handler reads fresh values without re-subscribing,
  // and so a re-render isn't triggered on every scroll tick.
  const isNearBottomRef = useRef(true)
  const didInitialScrollRef = useRef(false)
  const prevScrollHeightRef = useRef<number | null>(null)

  const visibleMessages = messages.slice(-visibleCount)
  const hasOlderMessages = visibleCount < messages.length

  // Auto-scroll to the bottom on the first paint and whenever a new message
  // arrives — but only if the user is already near the bottom, so we never yank
  // them down while they're reading older history.
  useEffect(() => {
    if (isNearBottomRef.current) {
      messageEndRef.current?.scrollIntoView({
        behavior: didInitialScrollRef.current ? 'smooth' : 'auto',
      })
    }
    didInitialScrollRef.current = true
  }, [messages, isTyping])

  // After older messages are prepended, the content above the viewport grows;
  // restore scrollTop so the user's view stays anchored instead of jumping.
  useLayoutEffect(() => {
    const el = listRef.current
    if (el && prevScrollHeightRef.current !== null) {
      el.scrollTop += el.scrollHeight - prevScrollHeightRef.current
      prevScrollHeightRef.current = null
    }
  }, [visibleCount])

  const handleScroll = (event: UIEvent<HTMLDivElement>) => {
    const el = event.currentTarget
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    isNearBottomRef.current = distanceFromBottom <= NEAR_BOTTOM_PX

    if (el.scrollTop <= TOP_LOAD_PX) {
      setVisibleCount((count) => {
        if (count >= messages.length) return count
        prevScrollHeightRef.current = el.scrollHeight
        return Math.min(count + PAGE_SIZE, messages.length)
      })
    }
  }

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

    // The user just acted — snap back to the bottom even if they'd scrolled up.
    isNearBottomRef.current = true
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
      window.dispatchEvent(new Event('refreshSchedule'))

    } catch (error: unknown) {
      console.error('Error communicating with the backend:', error)

      const message = error instanceof Error ? error.message : String(error)
      const errorMessage =
        message === 'API_KEY_MISSING'
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
        maxHeight: '1000px',
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
          ref={listRef}
          onScroll={handleScroll}
          data-testid="chat-scroll"
          sx={{
            flex: 1,
            minHeight: 0,
            overflowY: 'auto',
            overscrollBehavior: 'contain',
            display: 'flex',
            flexDirection: 'column',
            gap: 1.1,
            mb: 1.6,
            pr: 0.45,
          }}
        >
          {hasOlderMessages && (
            <Typography
              data-testid="chat-older-hint"
              variant="caption"
              sx={{ textAlign: 'center', color: '#9aa6bf', py: 0.5 }}
            >
              Scroll up to load earlier messages…
            </Typography>
          )}

          {visibleMessages.map((message) => (
            <Box
              key={message.message_id}
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
