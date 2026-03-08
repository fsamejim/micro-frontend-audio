import React from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import {
  AudioFile as AudioIcon,
  ExitToApp as LogoutIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { UserProfile } from './UserProfile';
import { Statistics } from './Statistics';

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  const handleNavigateToAudio = () => {
    window.location.href = '/audio';
  };

  const handleNavigateToYouTube = () => {
    window.location.href = '/youtube';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome back, {user?.username || 'User'}!
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Audio Translation Dashboard
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: { xs: '1fr', md: '1fr 2fr' }, mb: 3 }}>
        {/* User Profile Card */}
        <Paper sx={{ p: 2, height: '100%' }}>
          <UserProfile />
        </Paper>

        {/* Statistics Card */}
        <Paper sx={{ p: 2, height: '100%' }}>
          <Statistics />
        </Paper>
      </Box>

      {/* Quick Actions */}
      <Box>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' } }}>
            {/* Upload Audio Card */}
            <Box>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <AudioIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">
                      Process Audio
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Upload and translate audio files
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={handleNavigateToAudio}
                    startIcon={<AudioIcon />}
                  >
                    Go to Audio
                  </Button>
                </CardActions>
              </Card>
            </Box>

            {/* YouTube Download Card */}
            <Box>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <DownloadIcon color="secondary" sx={{ mr: 1 }} />
                    <Typography variant="h6">
                      YouTube
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Download audio/video from YouTube
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    variant="outlined"
                    color="secondary"
                    onClick={handleNavigateToYouTube}
                    startIcon={<DownloadIcon />}
                  >
                    Download
                  </Button>
                </CardActions>
              </Card>
            </Box>

            {/* Logout Card */}
            <Box>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <LogoutIcon color="error" sx={{ mr: 1 }} />
                    <Typography variant="h6">
                      Sign Out
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    End your current session
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    onClick={logout}
                    startIcon={<LogoutIcon />}
                  >
                    Logout
                  </Button>
                </CardActions>
              </Card>
            </Box>
        </Box>
      </Box>
    </Container>
  );
};