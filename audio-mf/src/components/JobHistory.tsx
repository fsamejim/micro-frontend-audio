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
    Visibility as ViewIcon,
    Replay as RetryIcon
} from '@mui/icons-material';
import { translationService } from '../services/translationService';
import type { TranslationJob } from '../types/translation';
import { useAuth } from '../contexts/AuthContext';

interface JobHistoryProps {
    onViewJob?: (jobId: string) => void;
}

export const JobHistory: React.FC<JobHistoryProps> = ({ onViewJob }) => {
    const { user } = useAuth();
    const [jobs, setJobs] = useState<TranslationJob[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [retryingJobs, setRetryingJobs] = useState<Set<string>>(new Set());
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

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

    const handleRetryJob = async (jobId: string, originalFilename: string) => {
        setError(null);
        setSuccessMessage(null);
        
        // Add job to retrying set
        setRetryingJobs(prev => new Set(prev.add(jobId)));
        
        try {
            await translationService.retryJob(jobId);
            setSuccessMessage(`Retry started for "${originalFilename}" from last successful step`);
            
            // Refresh jobs list after a short delay to show updated status
            setTimeout(() => {
                fetchJobs();
            }, 1000);
            
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to retry job';
            setError(`Retry failed: ${errorMessage}`);
        } finally {
            // Remove job from retrying set
            setRetryingJobs(prev => {
                const newSet = new Set(prev);
                newSet.delete(jobId);
                return newSet;
            });
        }
    };

    const getStatusColor = (status: string): 'primary' | 'secondary' | 'success' | 'error' | 'warning' => {
        switch (status) {
            case 'COMPLETED':
            case 'completed': 
                return 'success';
            case 'FAILED_PREPROCESSING_AUDIO_EN':
            case 'FAILED_TRANSCRIBING_EN':
            case 'FAILED_FORMATTING_TEXT_EN':
            case 'FAILED_TRANSLATING_CHUNKS_JP':
            case 'FAILED_MERGING_CHUNKS_JP':
            case 'FAILED_CLEANING_TEXT_JP':
            case 'FAILED_GENERATING_AUDIO_JP':
            case 'FAILED':
            case 'failed': 
                return 'error';
            case 'UPLOADED_EN':
            case 'uploaded': 
                return 'primary';
            default: 
                return 'warning';
        }
    };

    const getRetryStepFromStatus = (status: string): string => {
        switch (status) {
            case 'FAILED_PREPROCESSING_AUDIO_EN': return 'Audio Preprocessing';
            case 'FAILED_TRANSCRIBING_EN': return 'Transcription';
            case 'FAILED_FORMATTING_TEXT_EN': return 'Text Formatting';
            case 'FAILED_TRANSLATING_CHUNKS_JP': return 'Translation';
            case 'FAILED_MERGING_CHUNKS_JP': return 'Chunk Merging';
            case 'FAILED_CLEANING_TEXT_JP': return 'Text Cleaning';
            case 'FAILED_GENERATING_AUDIO_JP': return 'Audio Generation';
            case 'FAILED':
            case 'failed':
            default:
                return 'Failed Step';
        }
    };

    const isFailedStatus = (status: string): boolean => {
        return status.startsWith('FAILED_') || status === 'FAILED' || status === 'failed';
    };

    const getStatusText = (status: string): string => {
        switch (status) {
            case 'UPLOADED_EN': return 'Uploaded';
            case 'PREPROCESSING_AUDIO_EN': return 'Preprocessing Audio';
            case 'TRANSCRIBING_EN': return 'Transcribing';
            case 'FORMATTING_TEXT_EN': return 'Formatting Text';
            case 'TRANSLATING_CHUNKS_JP': return 'Translating';
            case 'MERGING_CHUNKS_JP': return 'Merging Chunks';
            case 'CLEANING_TEXT_JP': return 'Cleaning Text';
            case 'GENERATING_AUDIO_JP': return 'Generating Audio';
            case 'COMPLETED': return 'Completed';
            // Specific failure statuses
            case 'FAILED_PREPROCESSING_AUDIO_EN': return 'Failed: Audio Preprocessing';
            case 'FAILED_TRANSCRIBING_EN': return 'Failed: Transcription';
            case 'FAILED_FORMATTING_TEXT_EN': return 'Failed: Text Formatting';
            case 'FAILED_TRANSLATING_CHUNKS_JP': return 'Failed: Translation';
            case 'FAILED_MERGING_CHUNKS_JP': return 'Failed: Chunk Merging';
            case 'FAILED_CLEANING_TEXT_JP': return 'Failed: Text Cleaning';
            case 'FAILED_GENERATING_AUDIO_JP': return 'Failed: Audio Generation';
            case 'FAILED': return 'Failed';
            // Legacy support
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

            {/* Success Alert */}
            {successMessage && (
                <Alert severity="success" sx={{ mb: 2 }}>
                    {successMessage}
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
                                <Box display="flex" alignItems="center" gap={1}>
                                    {/* Retry Button for Failed Jobs */}
                                    {isFailedStatus(job.status) && (
                                        <Button
                                            variant="outlined"
                                            size="small"
                                            startIcon={<RetryIcon />}
                                            onClick={() => handleRetryJob(job.job_id, job.original_filename)}
                                            disabled={retryingJobs.has(job.job_id)}
                                            sx={{ 
                                                minWidth: 'auto',
                                                color: 'warning.main',
                                                borderColor: 'warning.main',
                                                '&:hover': {
                                                    borderColor: 'warning.dark',
                                                    backgroundColor: 'warning.light'
                                                }
                                            }}
                                        >
                                            {retryingJobs.has(job.job_id) 
                                                ? 'Retrying...' 
                                                : `Retry from ${getRetryStepFromStatus(job.status)}`
                                            }
                                        </Button>
                                    )}
                                    
                                    {/* View Job Button */}
                                    {onViewJob && (
                                        <IconButton 
                                            onClick={() => onViewJob(job.job_id)}
                                            sx={{ ml: 1 }}
                                        >
                                            <ViewIcon />
                                        </IconButton>
                                    )}
                                </Box>
                            </ListItem>
                            {index < jobs.length - 1 && <Divider />}
                        </React.Fragment>
                    ))}
                </List>
            )}
        </Paper>
    );
};