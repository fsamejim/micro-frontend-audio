import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  AudioFile as AudioIcon,
  Translate as TranslateIcon,
  History as HistoryIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingIcon
} from '@mui/icons-material';

export const Statistics: React.FC = () => {
  // Mock statistics data - in real app, this would come from API
  const stats = {
    totalJobs: 12,
    completedJobs: 10,
    inProgressJobs: 1,
    failedJobs: 1,
    totalMinutesProcessed: 45,
    averageProcessingTime: '3.2 min',
    successRate: 83
  };

  const recentActivity = [
    {
      id: 1,
      action: 'Audio translation completed',
      file: 'meeting-recording.mp3',
      time: '2 hours ago',
      status: 'success'
    },
    {
      id: 2,
      action: 'Audio upload started',
      file: 'interview-audio.wav',
      time: '1 day ago',
      status: 'processing'
    },
    {
      id: 3,
      action: 'Translation downloaded',
      file: 'presentation.mp3',
      time: '2 days ago',
      status: 'success'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Statistics & Activity
      </Typography>

      {/* Statistics Grid */}
      <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, mb: 3 }}>
        {/* Total Jobs */}
        <Box key="total-jobs">
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <AudioIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h5" component="div">
                {stats.totalJobs}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Total Jobs
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Completed */}
        <Box key="completed-jobs">
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <TranslateIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h5" component="div" color="success.main">
                {stats.completedJobs}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Completed
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* In Progress */}
        <Box key="progress-jobs">
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <ScheduleIcon color="warning" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h5" component="div" color="warning.main">
                {stats.inProgressJobs}
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                In Progress
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Success Rate */}
        <Box key="success-rate">
          <Card variant="outlined">
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <TrendingIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
              <Typography variant="h5" component="div">
                {stats.successRate}%
              </Typography>
              <Typography variant="body2" color="text.secondary" component="div">
                Success Rate
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Processing Stats */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom component="div">
          Processing Overview
        </Typography>
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary" component="div">
            Total audio processed: {stats.totalMinutesProcessed} minutes
          </Typography>
          <Typography variant="body2" color="text.secondary" component="div">
            Average processing time: {stats.averageProcessingTime}
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={stats.successRate} 
          sx={{ height: 8, borderRadius: 4 }}
        />
      </Box>

      {/* Recent Activity */}
      <Box>
        <Typography variant="subtitle2" gutterBottom component="div">
          Recent Activity
        </Typography>
        <List dense>
          {recentActivity.map((activity) => (
            <ListItem key={activity.id} divider>
              <ListItemIcon>
                <HistoryIcon color="action" />
              </ListItemIcon>
              <ListItemText
                primary={activity.action}
                secondary={
                  <>
                    <Typography variant="body2" color="text.secondary" component="span">
                      {activity.file}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary" component="span">
                      {activity.time}
                    </Typography>
                    {' '}
                    <Chip
                      label={activity.status}
                      size="small"
                      color={getStatusColor(activity.status) as any}
                      variant="outlined"
                    />
                  </>
                }
              />
            </ListItem>
          ))}
        </List>
      </Box>
    </Box>
  );
};