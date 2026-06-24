import { useEffect, useState } from 'react'
import { API_URL } from '../api'
import { useAuth } from '../contexts/AuthContext'
import type { Task } from '../types'

export function useTasks() {
  const { session } = useAuth()
  const [tasks, setTasks] = useState<Task[]>([])

  useEffect(() => {
    if (!session) return

    const loadTasks = async () => {
      try {
        const response = await fetch(`${API_URL}/tasks`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        })

        if (!response.ok) {
          throw new Error(`Failed to load tasks: ${response.status} ${response.statusText}`)
        }

        const data: unknown = await response.json()
        if (typeof data === 'object' && data !== null && 'tasks' in data && Array.isArray(data.tasks)) {
          setTasks(data.tasks as Task[])
        }
      } catch (error) {
        console.error('Failed to fetch tasks', error)
      }
    }

    void loadTasks()
    const interval = setInterval(() => {
      void loadTasks()
    }, 5000)

    return () => clearInterval(interval)
  }, [session])

  return tasks
}
