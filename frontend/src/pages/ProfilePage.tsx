import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Avatar,
  Divider,
  Alert,
  InputAdornment,
  IconButton,
  Chip,
  Stack,
  LinearProgress,
  Skeleton,
} from '@mui/material'
import {
  Email,
  Visibility,
  VisibilityOff,
  VpnKey,
  Check,
  ContentCopy,
  DeleteOutlined,
  CheckCircle,
  Cancel,
  HourglassEmpty,
} from '@mui/icons-material'

type KeyStatus = 'none' | 'validating' | 'valid' | 'invalid'

type ProfileUser = {
  name: string
  email: string
  avatarUrl?: string
  raw: { hd?: string }
}

function StatusChip({ status }: { status: KeyStatus }) {
  if (status === 'none') return null
  const map = {
    validating: { label: 'Validating…', color: 'default' as const, icon: <HourglassEmpty sx={{ fontSize: 14 }} /> },
    valid: { label: 'Valid key', color: 'success' as const, icon: <CheckCircle sx={{ fontSize: 14 }} /> },
    invalid: { label: 'Invalid key', color: 'error' as const, icon: <Cancel sx={{ fontSize: 14 }} /> },
  }
  const { label, color, icon } = map[status]
  return <Chip size="small" label={label} color={color} icon={icon} />
}

function avatarInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}

export default function ProfilePage() {
  const [user] = useState<ProfileUser | null>(null)
  const [loading] = useState(false)

  const [groqKey, setGroqKey] = useState(() => localStorage.getItem('groq_api_key') ?? '')
  const [showKey, setShowKey] = useState(false)
  const [keyStatus, setKeyStatus] = useState<KeyStatus>('none')
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [copied, setCopied] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const maskedKey =
    groqKey.length > 8 ? groqKey.slice(0, 4) + '••••••••' + groqKey.slice(-4) : groqKey

  const handleValidate = () => {
    if (!groqKey.trim() || !groqKey.startsWith('gsk_')) {
      setKeyStatus('invalid')
      setValidationError('Key must start with "gsk_". Get yours at console.groq.com.')
      return
    }

    setKeyStatus('validating')
    setValidationError(null)

    try {
      fetch('https://api.groq.com/openai/v1/models', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${groqKey}`,
          'content-type': 'application/json',
        },
      })
        .then((response) => {
          if (response.ok) {
            setKeyStatus('valid')
          } else {
            setKeyStatus('invalid')
            setValidationError('Invalid key. Please check your key and try again.')
          }
        })
        .catch(() => {
          setKeyStatus('invalid')
          setValidationError('Network error. Please try again later.')
        })
    } catch {
      setKeyStatus('invalid')
      setValidationError('Unexpected error. Please try again later.')
    }
  }

  const handleSave = () => {
    localStorage.setItem('groq_api_key', groqKey)
    setSaveSuccess(true)
    setTimeout(() => setSaveSuccess(false), 3000)
  }

  const handleClear = () => {
    setGroqKey('')
    setKeyStatus('none')
    localStorage.removeItem('groq_api_key')
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(groqKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const pageCardSx = {
    borderRadius: '20px',
    border: '1px solid #e1e7f2',
    bgcolor: '#ffffff',
    boxShadow: '0 20px 42px -32px rgba(43, 62, 103, 0.5)',
  }

  return (
    <Box sx={{ maxWidth: 860, mx: 'auto', px: { xs: 0.2, sm: 0.5 }, py: 0.2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      <Typography sx={{ fontWeight: 800, fontSize: { xs: '1.45rem', sm: '1.9rem' }, color: '#243251', letterSpacing: '-0.03em', mb: 0.5 }}>
        User Profile
      </Typography>

      <Card sx={pageCardSx}>
        <CardContent sx={{ p: { xs: 2.2, sm: 2.6 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5, mb: 2.4 }}>
            {loading ? (
              <Skeleton variant="circular" width={80} height={80} />
            ) : user && user.avatarUrl ? (
              <Avatar src={user.avatarUrl} sx={{ width: 80, height: 80 }} />
            ) : (
              <Avatar sx={{ width: 80, height: 80, bgcolor: '#dbe3ff', color: '#33457a', fontSize: '1.75rem', fontWeight: 800 }}>
                {user ? avatarInitials(user.name) : '?'}
              </Avatar>
            )}

            <Box>
              {loading ? (
                <>
                  <Skeleton width={180} height={32} />
                  <Skeleton width={120} height={20} sx={{ mt: 0.5 }} />
                </>
              ) : user ? (
                <>
                  <Typography sx={{ fontWeight: 800, fontSize: '1.4rem', color: '#22324f' }}>{user.name}</Typography>
                  <Typography variant="body2" sx={{ color: '#6b7892' }}>{user.email}</Typography>
                </>
              ) : (
                <>
                  <Typography sx={{ fontWeight: 700, color: '#8d98ad' }}>Not signed in</Typography>
                  <Typography variant="body2" sx={{ color: '#9aa5b8' }}>Sign in with Google to see your profile</Typography>
                </>
              )}
            </Box>
          </Box>

          {!loading && user && (
            <>
              <Divider sx={{ mb: 2.2, borderColor: '#e6ebf4' }} />
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.4 }}>
                  <Email fontSize="small" sx={{ color: '#60728f' }} />
                  <Box>
                    <Typography variant="caption" sx={{ color: '#7f8ba2' }}>Google Account</Typography>
                    <Typography variant="body2" sx={{ color: '#2f3d5d', fontWeight: 600 }}>{user.email}</Typography>
                  </Box>
                </Box>
                {user.raw.hd && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.4 }}>
                    <Box sx={{ width: 20, display: 'flex', justifyContent: 'center' }}>
                      <Typography variant="body2" sx={{ color: '#7f8ba2', fontWeight: 700 }}>@</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#7f8ba2' }}>Organisation Domain</Typography>
                      <Typography variant="body2" sx={{ color: '#2f3d5d', fontWeight: 600 }}>{user.raw.hd as string}</Typography>
                    </Box>
                  </Box>
                )}
              </Stack>
            </>
          )}
        </CardContent>
      </Card>

      <Card sx={pageCardSx}>
        <CardContent sx={{ p: { xs: 2.2, sm: 2.6 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.4 }}>
            <VpnKey sx={{ color: '#4f66ea' }} />
            <Typography sx={{ fontWeight: 700, fontSize: '1.05rem', color: '#22304f' }}>Groq API Key</Typography>
            <Box sx={{ ml: 'auto' }}>
              <StatusChip status={keyStatus} />
            </Box>
          </Box>
          <Typography variant="body2" sx={{ mb: 2.1, color: '#6a7690', lineHeight: 1.6 }}>
            Your key is stored only in this browser and never sent to any server. It powers AI features via Groq.
          </Typography>

          {keyStatus === 'validating' && <LinearProgress sx={{ mb: 2, borderRadius: 1, bgcolor: '#eaf0ff' }} />}

          <TextField
            fullWidth
            label="Groq API Key"
            placeholder="gsk_••••••••••••••••••••••••••••••••"
            value={showKey ? groqKey : groqKey ? maskedKey : ''}
            onChange={(e) => {
              setGroqKey(e.target.value)
              setKeyStatus('none')
            }}
            onFocus={() => setShowKey(true)}
            onBlur={() => setShowKey(false)}
            type={showKey ? 'text' : 'password'}
            size="small"
            sx={{
              mb: 2,
              '& .MuiOutlinedInput-root': {
                borderRadius: '12px',
                bgcolor: '#f9fbff',
                '& fieldset': { borderColor: '#d9e2f3' },
                '&:hover fieldset': { borderColor: '#c8d4ea' },
                '&.Mui-focused fieldset': { borderColor: '#7083f4' },
              },
            }}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowKey((v) => !v)} edge="end" size="small">
                      {showKey ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          {keyStatus === 'invalid' && validationError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {validationError}
            </Alert>
          )}

          {keyStatus === 'valid' && saveSuccess && (
            <Alert severity="success" icon={<Check />} sx={{ mb: 2 }}>
              API key saved successfully.
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              onClick={handleValidate}
              disabled={!groqKey.trim() || keyStatus === 'validating'}
              size="small"
              sx={{ textTransform: 'none', borderRadius: '10px', bgcolor: '#5a6df0', '&:hover': { bgcolor: '#4458dd' } }}
            >
              Validate
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<Check />}
              onClick={handleSave}
              disabled={!groqKey.trim() || keyStatus === 'validating'}
              size="small"
              sx={{ textTransform: 'none', borderRadius: '10px' }}
            >
              Save Key
            </Button>
            {groqKey && (
              <Button
                variant="outlined"
                startIcon={copied ? <Check /> : <ContentCopy />}
                onClick={handleCopy}
                size="small"
                sx={{ textTransform: 'none', borderRadius: '10px', borderColor: '#d0daed' }}
              >
                {copied ? 'Copied' : 'Copy'}
              </Button>
            )}
            {groqKey && (
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteOutlined />}
                onClick={handleClear}
                size="small"
                sx={{ textTransform: 'none', borderRadius: '10px' }}
              >
                Clear
              </Button>
            )}
          </Box>

          <Typography variant="caption" sx={{ display: 'block', mt: 1.8, color: '#8b96ac' }}>
            Stored in localStorage under groq_api_key. Clearing browser data will remove it.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
