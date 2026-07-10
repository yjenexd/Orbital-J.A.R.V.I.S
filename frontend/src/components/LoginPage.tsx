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
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        px: 2,
      }}
    >
      <Box
        sx={{
          width: 'min(520px, 100%)',
          borderRadius: '24px',
          border: '1px solid #dfe7f5',
          background: 'linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,250,255,0.97) 100%)',
          boxShadow: '0 28px 56px -38px rgba(44, 66, 114, 0.6)',
          p: { xs: 3, sm: 4 },
          textAlign: 'center',
        }}
      >
        <Box
          component="img"
          src="/jarvis-logo.png"
          alt="JARVIS icon"
          sx={{
            width: 84,
            height: 84,
            mx: 'auto',
            borderRadius: '20px',
            objectFit: 'cover',
            border: '1px solid #dbe3f3',
            mb: 2,
          }}
        />

        <Typography sx={{ fontWeight: 800, letterSpacing: '-0.03em', fontSize: { xs: '1.8rem', sm: '2.1rem' }, color: '#1c2740' }}>
          J².A.R.V.I.S
        </Typography>
        <Typography sx={{ mt: 0.7, mb: 3, color: '#6a7690', lineHeight: 1.6 }}>
          Your AI secretary for daily priorities, calendar clarity, and fast execution.
        </Typography>

        <Button
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <GoogleIcon />}
          onClick={handleGoogleLogin}
          disabled={loading}
          sx={{
            px: 3,
            py: 1.2,
            textTransform: 'none',
            fontSize: '0.97rem',
            fontWeight: 700,
            borderRadius: '12px',
            background: '#5a6df0',
            '&:hover': { background: '#4458dd' },
          }}
        >
          {loading ? 'Redirecting…' : 'Sign in with Google'}
        </Button>
      </Box>
    </Box>
  )
}
