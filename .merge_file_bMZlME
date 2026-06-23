import { Card, CardContent, Typography, Box, Checkbox, Chip } from '@mui/material';
import { CheckBox, Flag, RadioButtonUnchecked } from '@mui/icons-material';
import { useEffect, useMemo, useState } from 'react';
import { API_URL } from '../api';
import type { Task } from '../types';

export function TaskPanel() {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    const loadTasks = async () => {
      try {
        const response = await fetch(`${API_URL}/tasks`);

        if (!response.ok) {
          throw new Error(`Failed to load tasks: ${response.status} ${response.statusText}`);
        }

        const data: unknown = await response.json();

        if (
          typeof data === 'object' &&
          data !== null &&
          'tasks' in data &&
          Array.isArray(data.tasks)
        ) {
          setTasks(data.tasks as Task[]);
        }
      } catch (error) {
        console.error('Failed to fetch tasks', error);
      }
    };

    void loadTasks();

    const interval = setInterval(() => {
      void loadTasks();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const sortedTasks = useMemo(
    () => [...tasks].sort((a, b) => Number(a.completed) - Number(b.completed)),
    [tasks]
  );

  const getPriorityColor = (priority: string): 'error' | 'warning' | 'action' => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'action';
    }
  };

  return (
    <Card sx={{ display: 'flex', flexDirection: 'column', maxHeight: 600 }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', flex: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexShrink: 0 }}>
          <CheckBox color="primary" />
          <Typography variant="h6" color="primary">
            Tasks & Personal Goals
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, overflowY: 'auto' }}>
          {sortedTasks.map((task) => (
            <Box
              key={task.task_id}
              sx={{
                p: 1.5,
                borderRadius: 1,
                border: 1,
                borderColor: 'divider',
                bgcolor: task.completed ? 'action.hover' : 'background.paper',
                '&:hover': { bgcolor: 'action.hover' },
                transition: 'background-color 0.2s',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                <Checkbox
                  checked={task.completed}
                  icon={<RadioButtonUnchecked />}
                  checkedIcon={<CheckBox />}
                  sx={{ p: 0, mt: 0.5 }}
                />
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        textDecoration: task.completed ? 'line-through' : 'none',
                        color: task.completed ? 'text.secondary' : 'text.primary',
                      }}
                    >
                      {task.title}
                    </Typography>
                    <Flag
                      color={getPriorityColor(task.priority)}
                      sx={{ fontSize: 16, flexShrink: 0 }}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                    {task.source && (
                      <Chip label={task.source} size="small" variant="outlined" />
                    )}
                    {task.deadline && (
                      <Chip label={task.deadline} size="small" variant="outlined" />
                    )}

                    {task.priority_score !== undefined && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontStyle: 'italic', display: 'block', width: '100%', mt: 0.5 }}
                      >
                        Score: {task.priority_score}/100 - {task.triage_rationale}
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Box>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}
