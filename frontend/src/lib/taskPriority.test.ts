import { describe, it, expect } from 'vitest'
import { isTaskTriaging, normalizeTaskPriority } from './taskPriority'
import type { Task } from '../types'

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 1,
    title: 'Test task',
    source: '',
    deadline: '',
    completed: false,
    user_id: 'u1',
    priority: '',
    priority_score: 0,
    triage_rationale: null,
    ...overrides,
  }
}

describe('isTaskTriaging', () => {
  it('is true while the backend has not written a rationale yet', () => {
    expect(isTaskTriaging(makeTask({ triage_rationale: null }))).toBe(true)
    expect(isTaskTriaging(makeTask({ triage_rationale: undefined }))).toBe(true)
    expect(isTaskTriaging(makeTask({ triage_rationale: '   ' }))).toBe(true)
  })

  it('is false once a rationale exists (AI or fallback)', () => {
    expect(isTaskTriaging(makeTask({ triage_rationale: 'Due within 48 hours.' }))).toBe(false)
    expect(isTaskTriaging(makeTask({ triage_rationale: 'Standard sorting applied.' }))).toBe(false)
  })

  it('is false for a completed task even without a rationale', () => {
    expect(isTaskTriaging(makeTask({ completed: true, triage_rationale: null }))).toBe(false)
  })
})

describe('normalizeTaskPriority', () => {
  it('prefers an explicit priority string', () => {
    expect(normalizeTaskPriority(makeTask({ priority: 'HIGH' }))).toBe('high')
  })

  it('falls back to the numeric score thresholds', () => {
    expect(normalizeTaskPriority(makeTask({ priority: '', priority_score: 80 }))).toBe('high')
    expect(normalizeTaskPriority(makeTask({ priority: '', priority_score: 50 }))).toBe('medium')
    expect(normalizeTaskPriority(makeTask({ priority: '', priority_score: 10 }))).toBe('low')
  })
})
