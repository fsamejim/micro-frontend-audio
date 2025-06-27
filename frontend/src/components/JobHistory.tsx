import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    Button,
    List,
    ListItem,
    ListItemText,
    Chip,
    Alert,
    Divider,
    IconButton
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    History as HistoryIcon,
    Visibility as ViewIcon
} from '@mui/icons-material';
import { translationService } from '../services/translationService';
import { TranslationJob } from '../types/translation';
import { useAuth } from '../contexts/AuthContext';

interface JobHistoryProps {
    onViewJob?: (jobId: string) => void;
}

export const JobHistory: React.FC<JobHistoryProps> = ({ onViewJob }) => {
    const { user } = useAuth();
    const [jobs, setJobs] = useState<TranslationJob[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchJobs = async () => {
        if (!user) return;

        setLoading(true);
        setError(null);
        try {
            const response = await translationService.getUserJobs(user.id);
            setJobs(response.jobs);
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch jobs';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, [user]);

    const getStatusColor = (status: string): 'primary' | 'secondary' | 'success' | 'error' | 'warning' => {
        switch (status) {
            case 'completed': return 'success';
            case 'failed': return 'error';
            case 'uploaded': return 'primary';
            default: return 'warning';
        }
    };

    const getStatusText = (status: string): string => {
        switch (status) {
            case 'uploaded': return 'Uploaded';
            case 'preprocessing_audio_en': return 'Preprocessing';
            case 'transcribing_en': return 'Transcribing';
            case 'formatting_text_en': return 'Formatting';
            case 'translating_chunks_jp': return 'Translating';
            case 'merging_chunks_jp': return 'Merging';
            case 'cleaning_text_jp': return 'Cleaning';
            case 'generating_audio_jp': return 'Generating Audio';
            case 'completed': return 'Completed';
            case 'failed': return 'Failed';
            default: return status;
        }
    };

    const formatDate = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch {
            return dateString;
        }
    };

    if (!user) {
        return (
            <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
                <Alert severity="warning">
                    Please log in to view your job history.
                </Alert>
            </Paper>
        );
    }

    return (
        <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
            {/* Header */}
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Box display="flex" alignItems="center" gap={1}>
                    <HistoryIcon />
                    <Typography variant="h6">
                        Job History
                    </Typography>
                </Box>
                <Button 
                    onClick={fetchJobs} 
                    disabled={loading}
                    startIcon={<RefreshIcon />}
                    size="small"
                >
                    {loading ? 'Loading...' : 'Refresh'}
                </Button>
            </Box>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Jobs List */}
            {jobs.length === 0 ? (
                <Box textAlign="center" py={4}>
                    <Typography variant="body1" color="textSecondary">
                        No translation jobs found.
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                        Upload an audio file to start your first translation!
                    </Typography>
                </Box>
            ) : (
                <List>
                    {jobs.map((job, index) => (
                        <React.Fragment key={job.job_id}>
                            <ListItem alignItems="flex-start">
                                <ListItemText
                                    primary={
                                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                                            <Typography variant="subtitle1" component="span">
                                                {job.original_filename}
                                            </Typography>
                                            <Chip 
                                                label={getStatusText(job.status)} 
                                                color={getStatusColor(job.status)}
                                                size="small"
                                            />
                                        </Box>
                                    }
                                    secondary={
                                        <Box>
                                            <Typography variant="body2" color="textSecondary" gutterBottom>
                                                Job ID: {job.job_id}
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                Created: {formatDate(job.created_at || '')}
                                            </Typography>
                                            {job.completed_at && (
                                                <Typography variant="body2" color="textSecondary">
                                                    Completed: {formatDate(job.completed_at)}
                                                </Typography>
                                            )}
                                            <Box display="flex" alignItems="center" gap={1} mt={1}>
                                                <Typography variant="body2" color="textSecondary">
                                                    Progress: {job.progress}%
                                                </Typography>
                                                {job.status === 'completed' && (
                                                    <Typography variant="body2" color="success.main">
                                                        • {job.files?.length || 0} files available
                                                    </Typography>
                                                )}
                                            </Box>
                                        </Box>
                                    }
                                />
                                {onViewJob && (
                                    <IconButton 
                                        onClick={() => onViewJob(job.job_id)}
                                        sx={{ ml: 1 }}
                                    >
                                        <ViewIcon />
                                    </IconButton>
                                )}
                            </ListItem>
                            {index < jobs.length - 1 && <Divider />}
                        </React.Fragment>
                    ))}
                </List>
            )}
        </Paper>
    );
};