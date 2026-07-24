import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createElement } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { validateGroqKeyFormat } from '../groqKeyUtils'
import ProfilePage from '../../pages/ProfilePage'

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ session: null, loading: false }),
}))

vi.mock('../../lib/supabaseClient', () => ({
  supabase: { auth: { signOut: vi.fn() } },
}))

const makeLocalStorageMock = () => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
}

describe('validateGroqKeyFormat', () => {
  it('returns null for a valid gsk_ key', () => {
    expect(validateGroqKeyFormat('gsk_abc123')).toBeNull()
  })

  it('returns error message for key not starting with gsk_', () => {
    const err = validateGroqKeyFormat('password123')
    expect(err).not.toBeNull()
    expect(err).toContain('gsk_')
  })

  it('returns error message for a key with different provider prefix', () => {
    expect(validateGroqKeyFormat('sk-12345')).not.toBeNull()
  })

  it('returns error message for an empty string', () => {
    expect(validateGroqKeyFormat('')).not.toBeNull()
  })

  it('returns error message for a whitespace-only string', () => {
    expect(validateGroqKeyFormat('   ')).not.toBeNull()
  })
})

describe('Groq key localStorage persistence', () => {
  const mockStorage = makeLocalStorageMock()

  beforeEach(() => {
    mockStorage.clear()
    vi.stubGlobal('localStorage', mockStorage)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('persists key in localStorage on Save Key click', () => {
    render(createElement(ProfilePage))
    fireEvent.change(screen.getByLabelText('Groq API Key'), { target: { value: 'gsk_testkey' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Key' }))

    expect(mockStorage.getItem('groq_api_key')).toBe('gsk_testkey')
  })

  it('wipes key from localStorage on Clear click', () => {
    mockStorage.setItem('groq_api_key', 'gsk_testkey')
    render(createElement(ProfilePage))
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    expect(mockStorage.getItem('groq_api_key')).toBeNull()
  })
})
