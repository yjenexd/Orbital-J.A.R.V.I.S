import { useEffect, useState } from 'react'
import { API_URL } from '../api'
import { useAuth } from '../contexts/AuthContext'
import type { Task } from '../types'

export interface UseTasksResult {
  tasks: Task[]
  /** True until the first fetch settles, so the UI can show a skeleton on load. */
  isLoading: boolean
}

export function useTasks(): UseTasksResult {
  const { session } = useAuth()
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!session) return

    let cancelled = false

    const loadTasks = async () => {
      try {
        const response = await fetch(`${API_URL}/tasks`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        })

        if (!response.ok) {
          throw new Error(`Failed to load tasks: ${response.status} ${response.statusText}`)
        }

        const data: unknown = await response.json()
        if (cancelled) return
        if (typeof data === 'object' && data !== null && 'tasks' in data && Array.isArray(data.tasks)) {
          setTasks(data.tasks as Task[])
        }
      } catch (error) {
        console.error('Failed to fetch tasks', error)
      } finally {
        // Only the first fetch flips the loading flag; the 5s poll refreshes data
        // silently so the skeleton doesn't flash on every tick.
        if (!cancelled) setIsLoading(false)
      }
    }

    void loadTasks()
    const interval = setInterval(() => {
      void loadTasks()
    }, 5000)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [session])

  return { tasks, isLoading }
}
