import { Box, Button, Typography, CircularProgress } from '@mui/material'
import GoogleIcon from '@mui/icons-material/Google'
import { useState } from 'react'
import { supabase } from '../lib/supabaseClient'

export default function LoginPage() {
  const [loading, setLoading] = useState(false)

  const handleGoogleLogin = async () => {
    setLoading(true)
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin,
        scopes: 'https://www.googleapis.com/auth/calendar',
        queryParams: { access_type: 'offline', prompt: 'consent' },
      },
    })
  }

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        gap: 3,
      }}
    >
      <Typography variant="h4" sx={{ fontWeight: 'bold' }} color="primary">
        J².A.R.V.I.S
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Your AI Secretary. Sign in to continue.
      </Typography>
      <Button
        variant="contained"
        size="large"
        startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <GoogleIcon />}
        onClick={handleGoogleLogin}
        disabled={loading}
        sx={{ px: 4, py: 1.5, textTransform: 'none', fontSize: '1rem' }}
      >
        {loading ? 'Redirecting…' : 'Sign in with Google'}
      </Button>
    </Box>
  )
}
