import { Card, CardContent, Typography, Box, Checkbox, Chip } from '@mui/material';
import { CheckBox, Flag, RadioButtonUnchecked } from '@mui/icons-material';

interface Task {
  title: string;
  priority: 'high' | 'medium' | 'low';
  source: string;
  deadline?: string;
  completed: boolean;
}

export function TaskPanel() {
  const tasks: Task[] = [
    {
      title: 'Complete CS2040S Problem Set 3',
      priority: 'high',
      source: 'Email from Prof. Tan',
      deadline: 'Tomorrow, 11:59 PM',
      completed: false,
    },
    {
      title: 'Prepare presentation for project meeting',
      priority: 'high',
      source: 'Manual entry',
      deadline: 'Today, 2:00 PM',
      completed: false,
    },
    {
      title: 'Review lecture notes for MA1521',
      priority: 'medium',
      source: 'Conversation',
      deadline: 'Friday',
      completed: false,
    },
    {
      title: 'Submit group project proposal',
      priority: 'medium',
      source: 'Email from team',
      deadline: 'Next Monday',
      completed: false,
    },
    {
      title: 'Read Chapter 5 for CS2030S',
      priority: 'low',
      source: 'Manual entry',
      completed: true,
    },
  ];

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
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CheckBox color="primary" />
          <Typography variant="h6" color="primary">
            Tasks & Personal Goals
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {tasks.map((task, index) => (
            <Box
              key={index}
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
                    <Chip label={task.source} size="small" variant="outlined" />
                    {task.deadline && (
                      <Chip label={task.deadline} size="small" variant="outlined" />
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