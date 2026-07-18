import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { validateGroqKeyFormat } from '../groqKeyUtils'

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
  const store: Record<string, string> = {}
  const mockStorage = {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v },
    removeItem: (k: string) => { delete store[k] },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]) },
  }

  beforeEach(() => {
    mockStorage.clear()
    vi.stubGlobal('localStorage', mockStorage)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('persists key in localStorage on save', () => {
    localStorage.setItem('groq_api_key', 'gsk_testkey')
    expect(localStorage.getItem('groq_api_key')).toBe('gsk_testkey')
  })

  it('wipes key from localStorage on clear', () => {
    localStorage.setItem('groq_api_key', 'gsk_testkey')
    localStorage.removeItem('groq_api_key')
    expect(localStorage.getItem('groq_api_key')).toBeNull()
  })
})
