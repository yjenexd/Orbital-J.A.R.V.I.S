import { Box, Typography } from '@mui/material'
import { CheckCircle, WarningAmber } from '@mui/icons-material'
import { useMemo } from 'react'
import { useTasks } from '../hooks/useTasks'
import { normalizeTaskPriority } from '../lib/taskPriority'

function StatCard({
  value,
  label,
  subtitle,
  tone,
}: {
  value: string
  label: string
  subtitle: string
  tone: 'indigo' | 'amber'
}) {
  const palette =
    tone === 'indigo'
      ? {
          valueColor: '#6f46e8',
          chipBg: '#efe9ff',
          icon: <CheckCircle sx={{ color: '#7b53ec', fontSize: 20 }} />,
        }
      : {
          valueColor: '#cd7b00',
          chipBg: '#fff3dc',
          icon: <WarningAmber sx={{ color: '#de9200', fontSize: 20 }} />,
        }

  return (
    <Box
      sx={{
        p: 2,
        borderRadius: '16px',
        border: '1px solid #e4e9f3',
        bgcolor: '#ffffff',
        boxShadow: '0 16px 30px -30px rgba(41, 58, 99, 0.5)',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1 }}>
        <Typography sx={{ fontSize: '2rem', fontWeight: 800, color: palette.valueColor, lineHeight: 1 }}>
          {value}
        </Typography>
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: '12px',
            bgcolor: palette.chipBg,
            display: 'grid',
            placeItems: 'center',
          }}
        >
          {palette.icon}
        </Box>
      </Box>

      <Typography sx={{ fontWeight: 700, fontSize: '1rem', color: '#1f2b47' }}>{label}</Typography>
      <Typography sx={{ mt: 0.35, color: '#76839e', fontSize: '0.9rem' }}>{subtitle}</Typography>
    </Box>
  )
}

export function DashboardSummary() {
  const tasks = useTasks()

  const { doneCount, totalCount, urgentCount } = useMemo(() => {
    const total = tasks.length
    const done = tasks.filter((task) => task.completed).length
    const urgent = tasks.filter((task) => !task.completed && normalizeTaskPriority(task) === 'high').length

    return {
      doneCount: done,
      totalCount: total,
      urgentCount: urgent,
    }
  }, [tasks])

  const dateLabel = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  }).format(new Date())

  return (
    <Box>
      <Typography sx={{ fontWeight: 800, fontSize: { xs: '1.8rem', sm: '2rem' }, color: '#152442', letterSpacing: '-0.02em' }}>
        Dashboard
      </Typography>
      <Typography sx={{ mt: 0.35, color: '#66748f', fontSize: '1rem' }}>
        {dateLabel} - here&apos;s your day at a glance
      </Typography>

      <Box sx={{ mt: 1.4, display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1.2 }}>
        <StatCard
          value={`${doneCount}/${totalCount}`}
          label="Tasks Done"
          subtitle={totalCount === 0 ? 'No tasks in your list yet' : 'Matches your current task panel'}
          tone="indigo"
        />
        <StatCard
          value={String(urgentCount)}
          label="Urgent Items"
          subtitle={urgentCount === 0 ? 'No high-priority tasks right now' : 'High-priority tasks in your task panel'}
          tone="amber"
        />
      </Box>
    </Box>
  )
}
