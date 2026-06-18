import { useState } from 'react';
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
} from '@mui/material';
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
} from '@mui/icons-material';
// import { useAuth } from '../contexts/AuthContext'; // TODO: implement AuthContext

type KeyStatus = 'none' | 'validating' | 'valid' | 'invalid';

type ProfileUser = {
  name: string;
  email: string;
  avatarUrl?: string;
  raw: { hd?: string };
};

function StatusChip({ status }: { status: KeyStatus }) {
  if (status === 'none') return null;
  const map = {
    validating: { label: 'Validating…', color: 'default' as const, icon: <HourglassEmpty sx={{ fontSize: 14 }} /> },
    valid: { label: 'Valid key', color: 'success' as const, icon: <CheckCircle sx={{ fontSize: 14 }} /> },
    invalid: { label: 'Invalid key', color: 'error' as const, icon: <Cancel sx={{ fontSize: 14 }} /> },
  };
  const { label, color, icon } = map[status];
  return <Chip size="small" label={label} color={color} icon={icon} />;
}

function avatarInitials(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
}

export default function ProfilePage() {
  // TODO: replace stubs with useAuth() once AuthContext is implemented
  const [user] = useState<ProfileUser | null>(null);
  const [loading] = useState(false);

  const [groqKey, setGroqKey] = useState(() => localStorage.getItem('groq_api_key') ?? '');
  const [showKey, setShowKey] = useState(false);
  const [keyStatus, setKeyStatus] = useState<KeyStatus>('none');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [copied, setCopied] = useState(false);

  const maskedKey =
    groqKey.length > 8 ? groqKey.slice(0, 4) + '••••••••' + groqKey.slice(-4) : groqKey;

  const handleValidate = () => {
    if (!groqKey.trim()) { setKeyStatus('invalid'); return; }
    setKeyStatus('validating');
    setTimeout(() => {
      setKeyStatus(groqKey.startsWith('gsk_') ? 'valid' : 'invalid');
    }, 1200);
  };

  const handleSave = () => {
    localStorage.setItem('groq_api_key', groqKey);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  const handleClear = () => {
    setGroqKey('');
    setKeyStatus('none');
    localStorage.removeItem('groq_api_key');
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(groqKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box sx={{ maxWidth: 760, mx: 'auto', px: 3, py: 4, display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
        User Profile
      </Typography>

      {/* Identity card */}
      <Card variant="outlined">
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 3 }}>
            {loading ? (
              <Skeleton variant="circular" width={80} height={80} />
            ) : user && user.avatarUrl ? (
              <Avatar src={user.avatarUrl} sx={{ width: 80, height: 80 }} />
            ) : (
              <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main', fontSize: '1.75rem', fontWeight: 'bold' }}>
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
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{user.name}</Typography>
                  <Typography variant="body2" color="text.secondary">{user.email}</Typography>
                </>
              ) : (
                <>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }} color="text.disabled">Not signed in</Typography>
                  <Typography variant="body2" color="text.disabled">Sign in with Google to see your profile</Typography>
                </>
              )}
            </Box>
          </Box>

          {!loading && user && (
            <>
              <Divider sx={{ mb: 2.5 }} />
              <Stack spacing={2}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Email fontSize="small" color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">Google Account</Typography>
                    <Typography variant="body2">{user.email}</Typography>
                  </Box>
                </Box>
                {user.raw.hd && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{ width: 20, display: 'flex', justifyContent: 'center' }}>
                      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 'bold' }}>@</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Organisation Domain</Typography>
                      <Typography variant="body2">{user.raw.hd as string}</Typography>
                    </Box>
                  </Box>
                )}
              </Stack>
            </>
          )}
        </CardContent>
      </Card>

      {/* Groq API Key card */}
      <Card variant="outlined">
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <VpnKey color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>Groq API Key</Typography>
            <Box sx={{ ml: 'auto' }}>
              <StatusChip status={keyStatus} />
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
            Your key is stored only in this browser and never sent to any server. It powers all AI features via the Groq API.
          </Typography>

          {keyStatus === 'validating' && <LinearProgress sx={{ mb: 2, borderRadius: 1 }} />}

          <TextField
            fullWidth
            label="Groq API Key"
            placeholder="gsk_••••••••••••••••••••••••••••••••"
            value={showKey ? groqKey : groqKey ? maskedKey : ''}
            onChange={(e) => {
              setGroqKey(e.target.value);
              setKeyStatus('none');
            }}
            onFocus={() => setShowKey(true)}
            onBlur={() => setShowKey(false)}
            type={showKey ? 'text' : 'password'}
            size="small"
            sx={{ mb: 2 }}
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

          {keyStatus === 'invalid' && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Key must start with <strong>gsk_</strong>. Get yours at console.groq.com.
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
            >
              Save Key
            </Button>
            {groqKey && (
              <Button
                variant="outlined"
                startIcon={copied ? <Check /> : <ContentCopy />}
                onClick={handleCopy}
                size="small"
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
              >
                Clear
              </Button>
            )}
          </Box>

          <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 2 }}>
            Stored in <code>localStorage</code> under <code>groq_api_key</code>. Clearing browser data will remove it.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
