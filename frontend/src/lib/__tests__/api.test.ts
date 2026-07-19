import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { fetchWithGroqKey } from '../../api'

const makeLocalStorageMock = () => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
}

describe('fetchWithGroqKey', () => {
  const mockStorage = makeLocalStorageMock()

  beforeEach(() => {
    mockStorage.clear()
    vi.stubGlobal('localStorage', mockStorage)
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('throws API_KEY_MISSING when no key is in localStorage', async () => {
    await expect(fetchWithGroqKey('/test')).rejects.toThrow('API_KEY_MISSING')
  })

  it('appends X-Groq-Api-Key header from localStorage', async () => {
    mockStorage.setItem('groq_api_key', 'gsk_testkey123')

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    })
    vi.stubGlobal('fetch', mockFetch)

    await fetchWithGroqKey('http://localhost/test')

    const [, options] = mockFetch.mock.calls[0] as [string, RequestInit]
    expect((options.headers as Record<string, string>)['X-Groq-Api-Key']).toBe('gsk_testkey123')
  })
})
