import { describe, it, expect } from 'vitest'
import { normalizeTaskPriority } from '../taskPriority'
import type { Task } from '../../types'

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    task_id: 1,
    user_id: 'u1',
    title: 'Test task',
    priority: null,
    priority_score: null,
    triage_rationale: null,
    source: 'manual',
    deadline: null,
    completed: false,
    ...overrides,
  } as unknown as Task
}

describe('normalizeTaskPriority', () => {
  it('returns direct string when priority is high', () => {
    expect(normalizeTaskPriority(makeTask({ priority: 'high' }))).toBe('high')
  })

  it('returns direct string when priority is medium', () => {
    expect(normalizeTaskPriority(makeTask({ priority: 'medium' }))).toBe('medium')
  })

  it('returns direct string when priority is low', () => {
    expect(normalizeTaskPriority(makeTask({ priority: 'low' }))).toBe('low')
  })

  it('falls back to score >= 70 as high', () => {
    expect(normalizeTaskPriority(makeTask({ priority_score: 85 }))).toBe('high')
  })

  it('falls back to score >= 40 as medium', () => {
    expect(normalizeTaskPriority(makeTask({ priority_score: 55 }))).toBe('medium')
  })

  it('falls back to score < 40 as low', () => {
    expect(normalizeTaskPriority(makeTask({ priority_score: 20 }))).toBe('low')
  })

  it('defaults to low when no priority and no score', () => {
    expect(normalizeTaskPriority(makeTask())).toBe('low')
  })
})
