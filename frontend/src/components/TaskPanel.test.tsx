import React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { TaskPanel } from './TaskPanel'
import type { Task } from '../types'

// Authenticated session so useTasks starts fetching.
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ session: { user: { id: 'u1' }, access_token: 'tok' }, loading: false }),
}))

function makeTask(overrides: Partial<Task>): Task {
  return {
    task_id: 1,
    title: 'Task',
    source: '',
    deadline: '',
    completed: false,
    user_id: 'u1',
    priority: 'high',
    priority_score: 90,
    triage_rationale: 'Due soon.',
    ...overrides,
  }
}

/** A fetch mock whose response resolves only when we call `resolve()` — lets us
 *  hold the request open to simulate high backend latency. */
function deferredTasksFetch(tasks: Task[]) {
  let resolve!: () => void
  const gate = new Promise<void>((r) => (resolve = r))
  const fetchMock = vi.fn(async () => {
    await gate
    return { ok: true, json: async () => ({ tasks }) } as unknown as Response
  })
  return { fetchMock, resolve }
}

beforeEach(() => {
  vi.useRealTimers()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('TaskPanel loading state', () => {
  it('shows skeleton loaders while the backend request is in flight, then the tasks', async () => {
    const { fetchMock, resolve } = deferredTasksFetch([makeTask({ task_id: 7, title: 'Finish slides' })])
    vi.stubGlobal('fetch', fetchMock)

    render(<TaskPanel />)

    // High-latency window: request pending -> skeletons visible, no real task yet.
    expect(screen.getAllByTestId('task-skeleton').length).toBeGreaterThan(0)
    expect(screen.queryByText('Finish slides')).toBeNull()

    // Backend responds -> skeletons replaced by the task.
    resolve()
    await waitFor(() => expect(screen.getByText('Finish slides')).toBeInTheDocument())
    expect(screen.queryByTestId('task-skeleton')).toBeNull()
  })

  it('shows a "Prioritizing…" indicator only for tasks still being triaged', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        tasks: [
          makeTask({ task_id: 1, title: 'Being scored', triage_rationale: null }),
          makeTask({ task_id: 2, title: 'Already scored', triage_rationale: 'Due within 48 hours.' }),
        ],
      }),
    }) as unknown as Response)
    vi.stubGlobal('fetch', fetchMock)

    render(<TaskPanel />)

    await waitFor(() => expect(screen.getByText('Being scored')).toBeInTheDocument())

    // Exactly one task is mid-triage, and its rationale line is hidden.
    expect(screen.getAllByTestId('task-triaging')).toHaveLength(1)
    expect(screen.getByText(/Prioritizing/)).toBeInTheDocument()
    // The scored task shows its rationale.
    expect(screen.getByText(/Due within 48 hours/)).toBeInTheDocument()
  })
})
