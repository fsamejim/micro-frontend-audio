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
                return 'success';
            case 'FAILED_PREPROCESSING_AUDIO':
            case 'FAILED_TRANSCRIBING_SOURCE':
            case 'FAILED_FORMATTING_SOURCE_TEXT':
            case 'FAILED_TRANSLATING_TO_TARGET':
            case 'FAILED_MERGING_TARGET_CHUNKS':
            case 'FAILED_CLEANING_TARGET_TEXT':
            case 'FAILED_GENERATING_TARGET_AUDIO':
            case 'FAILED':
                return 'error';
            case 'UPLOADED':
                return 'primary';
            default:
                return 'warning';
        }
    };

    const getRetryStepFromStatus = (status: string): string => {
        switch (status) {
            case 'FAILED_PREPROCESSING_AUDIO': return 'Audio Preprocessing';
            case 'FAILED_TRANSCRIBING_SOURCE': return 'Transcription';
            case 'FAILED_FORMATTING_SOURCE_TEXT': return 'Text Formatting';
            case 'FAILED_TRANSLATING_TO_TARGET': return 'Translation';
            case 'FAILED_MERGING_TARGET_CHUNKS': return 'Chunk Merging';
            case 'FAILED_CLEANING_TARGET_TEXT': return 'Text Cleaning';
            case 'FAILED_GENERATING_TARGET_AUDIO': return 'Audio Generation';
            case 'FAILED':
            default:
                return 'Failed Step';
        }
    };

    const isFailedStatus = (status: string): boolean => {
        return status.startsWith('FAILED_') || status === 'FAILED';
    };

    const getStatusText = (status: string): string => {
        switch (status) {
            case 'UPLOADED': return 'Uploaded';
            case 'PREPROCESSING_AUDIO': return 'Preprocessing Audio';
            case 'TRANSCRIBING_SOURCE': return 'Transcribing';
            case 'FORMATTING_SOURCE_TEXT': return 'Formatting Text';
            case 'TRANSLATING_TO_TARGET': return 'Translating';
            case 'MERGING_TARGET_CHUNKS': return 'Merging Chunks';
            case 'CLEANING_TARGET_TEXT': return 'Cleaning Text';
            case 'GENERATING_TARGET_AUDIO': return 'Generating Audio';
            case 'COMPLETED': return 'Completed';
            // Specific failure statuses
            case 'FAILED_PREPROCESSING_AUDIO': return 'Failed: Audio Preprocessing';
            case 'FAILED_TRANSCRIBING_SOURCE': return 'Failed: Transcription';
            case 'FAILED_FORMATTING_SOURCE_TEXT': return 'Failed: Text Formatting';
            case 'FAILED_TRANSLATING_TO_TARGET': return 'Failed: Translation';
            case 'FAILED_MERGING_TARGET_CHUNKS': return 'Failed: Chunk Merging';
            case 'FAILED_CLEANING_TARGET_TEXT': return 'Failed: Text Cleaning';
            case 'FAILED_GENERATING_TARGET_AUDIO': return 'Failed: Audio Generation';
            case 'FAILED': return 'Failed';
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
                                                {job.status === 'COMPLETED' && (
                                                    <Typography variant="body2" color="success.main">
                                                        • {job.files?.length || 0} files available
                                                    </Typography>
                                                )}
                                            </Box>
                                            {/* Audio Versions Info */}
                                            {job.audio_versions && job.audio_versions.length > 0 && (
                                                <Box sx={{ mt: 1, pl: 1, borderLeft: '2px solid #e0e0e0' }}>
                                                    <Typography variant="caption" color="textSecondary" fontWeight="bold">
                                                        Audio Versions:
                                                    </Typography>
                                                    {job.audio_versions.map((version) => {
                                                        const voiceEntries = Object.entries(version.voice_mappings || {});
                                                        const voiceInfo = voiceEntries.length > 0
                                                            ? voiceEntries.map(([speaker, voice]) => `${speaker}: ${voice}`).join(', ')
                                                            : 'Default voices';
                                                        return (
                                                            <Typography key={version.version} variant="caption" display="block" color="textSecondary" sx={{ ml: 1 }}>
                                                                v{version.version}: {version.speaking_rate}x speed | {voiceInfo}
                                                            </Typography>
                                                        );
                                                    })}
                                                </Box>
                                            )}
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