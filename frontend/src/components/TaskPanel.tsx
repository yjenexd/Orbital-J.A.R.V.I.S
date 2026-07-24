import { Card, CardContent, Typography, Box, Checkbox, Chip, Skeleton, CircularProgress } from '@mui/material'
import { CheckBox, RadioButtonUnchecked } from '@mui/icons-material'
import { useMemo } from 'react'
import { useTasks } from '../hooks/useTasks'
import { normalizeTaskPriority, isTaskTriaging } from '../lib/taskPriority'

type PriorityTheme = {
  itemBg: string
  itemBorder: string
  titleColor: string
  chipBg: string
  chipBorder: string
  chipColor: string
}

function getPriorityTheme(priority: 'high' | 'medium' | 'low', completed: boolean): PriorityTheme {
  if (completed) {
    return {
      itemBg: '#f2f4f8',
      itemBorder: '#e3e8f1',
      titleColor: '#8b97ab',
      chipBg: '#ebf0f8',
      chipBorder: '#dde5f1',
      chipColor: '#8b97ab',
    }
  }

  if (priority === 'high') {
    return {
      itemBg: '#fff3f4',
      itemBorder: '#f3c8cd',
      titleColor: '#5c3640',
      chipBg: '#ffe6e9',
      chipBorder: '#f6c5cc',
      chipColor: '#cc4e60',
    }
  }

  if (priority === 'medium') {
    return {
      itemBg: '#fff9ec',
      itemBorder: '#eed9a8',
      titleColor: '#5e4f2f',
      chipBg: '#fff1cf',
      chipBorder: '#efd8a0',
      chipColor: '#bb8b2b',
    }
  }

  return {
    itemBg: '#f2f7ff',
    itemBorder: '#d5e3fb',
    titleColor: '#324972',
    chipBg: '#e7f0ff',
    chipBorder: '#cfddf9',
    chipColor: '#4b78c7',
  }
}

function formatPriorityLabel(priority: 'high' | 'medium' | 'low') {
  if (priority === 'high') return 'High'
  if (priority === 'medium') return 'Med'
  return 'Low'
}

function TaskSkeleton() {
  return (
    <Box data-testid="task-skeleton" sx={{ p: 1.3, borderRadius: '12px', border: '1px solid #e9eef7', bgcolor: '#fafbff' }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.1 }}>
        <Skeleton variant="circular" width={20} height={20} />
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="70%" height={20} />
          <Skeleton variant="rounded" width={48} height={18} sx={{ mt: 0.8 }} />
        </Box>
      </Box>
    </Box>
  )
}

export function TaskPanel() {
  const { tasks, isLoading } = useTasks()

  const sortedTasks = useMemo(
    () => [...tasks].sort((a, b) => Number(a.completed) - Number(b.completed)),
    [tasks]
  )

  const completedCount = useMemo(
    () => sortedTasks.filter((task) => task.completed).length,
    [sortedTasks]
  )

  const showSkeleton = isLoading && sortedTasks.length === 0

  return (
    <Card
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: 430,
        borderRadius: '20px',
        border: '1px solid #e1e7f2',
        bgcolor: '#ffffff',
        boxShadow: '0 18px 38px -30px rgba(50, 72, 117, 0.45)',
      }}
    >
      <CardContent sx={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: 1, p: 2.25 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexShrink: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckBox sx={{ color: '#43b883' }} />
            <Typography sx={{ color: '#22304f', fontWeight: 700, fontSize: { xs: '1.18rem', sm: '1.3rem' } }}>
              Tasks & Goals
            </Typography>
          </Box>

          <Typography sx={{ color: '#7a87a0', fontWeight: 700, fontSize: '0.78rem' }}>
            {completedCount}/{sortedTasks.length} done
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, overflowY: 'auto', pr: 0.5 }}>
          {showSkeleton &&
            Array.from({ length: 4 }).map((_, index) => <TaskSkeleton key={`skeleton-${index}`} />)}

          {!showSkeleton &&
            sortedTasks.map((task) => {
            const priority = normalizeTaskPriority(task)
            const theme = getPriorityTheme(priority, task.completed)
            const triaging = isTaskTriaging(task)

            return (
              <Box
                key={task.task_id}
                sx={{
                  p: 1.3,
                  borderRadius: '12px',
                  border: `1px solid ${theme.itemBorder}`,
                  bgcolor: theme.itemBg,
                  '&:hover': { filter: 'brightness(0.99)' },
                  transition: 'filter 0.2s ease',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.1 }}>
                  <Checkbox
                    checked={task.completed}
                    icon={<RadioButtonUnchecked />}
                    checkedIcon={<CheckBox />}
                    sx={{ p: 0, mt: 0.15, color: '#9eabc3', '&.Mui-checked': { color: '#43b883' } }}
                  />

                  <Box sx={{ flex: 1 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 700,
                        textDecoration: task.completed ? 'line-through' : 'none',
                        color: theme.titleColor,
                        fontSize: '0.92rem',
                        lineHeight: 1.45,
                      }}
                    >
                      {task.title}
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 0.6, mt: 0.8, flexWrap: 'wrap', alignItems: 'center' }}>
                      {triaging ? (
                        <Box
                          data-testid="task-triaging"
                          sx={{ display: 'flex', alignItems: 'center', gap: 0.6 }}
                        >
                          <CircularProgress size={13} thickness={5} sx={{ color: '#8b97ab' }} />
                          <Typography variant="caption" sx={{ color: '#8b97ab', fontWeight: 700 }}>
                            Prioritizing…
                          </Typography>
                        </Box>
                      ) : (
                        <Chip
                          label={formatPriorityLabel(priority)}
                          size="small"
                          sx={{
                            height: 21,
                            bgcolor: theme.chipBg,
                            color: theme.chipColor,
                            border: `1px solid ${theme.chipBorder}`,
                            fontWeight: 700,
                            '& .MuiChip-label': { px: 0.8, fontSize: '0.7rem' },
                          }}
                        />
                      )}

                      {task.deadline && (
                        <Typography variant="caption" sx={{ color: '#7d8aa4', fontWeight: 600, alignSelf: 'center' }}>
                          {task.deadline}
                        </Typography>
                      )}

                      {task.source && (
                        <Typography variant="caption" sx={{ color: '#6e7ca0', fontWeight: 600, alignSelf: 'center' }}>
                          {task.source}
                        </Typography>
                      )}
                    </Box>

                    {!triaging && task.priority_score !== undefined && task.triage_rationale && (
                      <Typography
                        variant="caption"
                        sx={{ color: '#7f8ca6', display: 'block', mt: 0.45 }}
                      >
                        {task.priority_score}/100 - {task.triage_rationale}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Box>
            )
          })}
        </Box>
      </CardContent>
    </Card>
  )
}
