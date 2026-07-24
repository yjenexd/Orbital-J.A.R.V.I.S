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

/**
 * A task is "triaging" while the async background triage job is still scoring it.
 * The backend writes a triage_rationale once scoring finishes (whether the AI
 * succeeded or the neutral fallback was applied), so a missing rationale is our
 * signal that the priority is still being computed on the backend.
 */
export function isTaskTriaging(task: Task): boolean {
  if (task.completed) return false
  const rationale = task.triage_rationale
  return rationale === null || rationale === undefined || rationale.trim() === ''
}
