import type { Task } from '../types'

export type NormalizedPriority = 'high' | 'medium' | 'low'

export function normalizeTaskPriority(task: Task): NormalizedPriority {
  const direct = task.priority?.toLowerCase()
  if (direct === 'high' || direct === 'medium' || direct === 'low') return direct

  const score = task.priority_score ?? 0
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}
