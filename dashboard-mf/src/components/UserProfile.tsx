import React from 'react';
import {
  Box,
  Typography,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  AccountCircle as AccountIcon,
  VerifiedUser as VerifiedIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

export const UserProfile: React.FC = () => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" p={2}>
        <Typography variant="body1" color="text.secondary">
          Please log in to view your profile
        </Typography>
      </Box>
    );
  }

  // Generate avatar initials
  const getInitials = (username: string) => {
    return username
      .split(' ')
      .map(name => name.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        User Profile
      </Typography>
      
      {/* Avatar and Basic Info */}
      <Box display="flex" flexDirection="column" alignItems="center" mb={3}>
        <Avatar
          sx={{ 
            width: 80, 
            height: 80, 
            mb: 2,
            bgcolor: 'primary.main',
            fontSize: '1.5rem'
          }}
        >
          {getInitials(user.username)}
        </Avatar>
        
        <Typography variant="h6" textAlign="center">
          {user.username}
        </Typography>
        
        <Chip
          icon={<VerifiedIcon />}
          label="Active User"
          color="success"
          size="small"
          sx={{ mt: 1 }}
        />
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* User Details */}
      <List dense>
        <ListItem>
          <ListItemIcon>
            <AccountIcon color="primary" />
          </ListItemIcon>
          <ListItemText
            primary="User ID"
            secondary={`#${user.id}`}
          />
        </ListItem>
        
        <ListItem>
          <ListItemIcon>
            <PersonIcon color="primary" />
          </ListItemIcon>
          <ListItemText
            primary="Username"
            secondary={user.username}
          />
        </ListItem>
        
        <ListItem>
          <ListItemIcon>
            <EmailIcon color="primary" />
          </ListItemIcon>
          <ListItemText
            primary="Email"
            secondary={user.email}
          />
        </ListItem>
      </List>

      <Divider sx={{ my: 2 }} />

      {/* Account Status */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Account Status
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip
            label="Authenticated"
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            label="Active"
            color="primary"
            size="small"
            variant="outlined"
          />
        </Box>
      </Box>
    </Box>
  );
};