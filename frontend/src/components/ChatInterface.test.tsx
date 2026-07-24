import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { ChatInterface } from './ChatInterface'
import type { ChatMessage } from '../types'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ session: { user: { id: 'u1' }, access_token: 'tok' }, loading: false }),
}))

function makeHistory(count: number): ChatMessage[] {
  return Array.from({ length: count }, (_, i) => ({
    message_id: i,
    user_id: 'u1',
    content: `msg-${i}`,
    role: i % 2 === 0 ? 'system' : 'user',
    created_at: String(i),
  }))
}

function stubHistoryFetch(messages: ChatMessage[]) {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({ messages }),
  }) as unknown as Response)
  vi.stubGlobal('fetch', fetchMock)
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('ChatInterface scrolling', () => {
  it('auto-scrolls to the bottom once history loads', async () => {
    const scrollSpy = vi.spyOn(HTMLElement.prototype, 'scrollIntoView').mockImplementation(() => {})
    stubHistoryFetch(makeHistory(5))

    render(<ChatInterface />)

    await waitFor(() => expect(screen.getByText('msg-4')).toBeInTheDocument())
    expect(scrollSpy).toHaveBeenCalled()
  })

  it('lazy-loads older messages when the user scrolls to the top', async () => {
    stubHistoryFetch(makeHistory(50))

    render(<ChatInterface />)

    // Only the most recent page (30) renders initially: newest present, oldest not.
    await waitFor(() => expect(screen.getByText('msg-49')).toBeInTheDocument())
    expect(screen.queryByText('msg-0')).toBeNull()
    expect(screen.getByTestId('chat-older-hint')).toBeInTheDocument()

    // Scrolling to the top (scrollTop 0 in jsdom) reveals the next page.
    const scrollSpy = vi.spyOn(HTMLElement.prototype, 'scrollIntoView').mockImplementation(() => {})
    fireEvent.scroll(screen.getByTestId('chat-scroll'))

    await waitFor(() => expect(screen.getByText('msg-0')).toBeInTheDocument())
    // All loaded now, so the "load earlier" hint is gone...
    expect(screen.queryByTestId('chat-older-hint')).toBeNull()
    // ...and revealing older history must NOT yank the view to the bottom.
    expect(scrollSpy).not.toHaveBeenCalled()
  })
})
