import React, { useState, useEffect } from 'react';
import {
    Box,
    Paper,
    Typography,
    LinearProgress,
    Button,
    Chip,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    Alert,
    Collapse
} from '@mui/material';
import {
    Download as DownloadIcon,
    Refresh as RefreshIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { translationService } from '../services/translationService';
import { JobStatusResponse, TranslationFile } from '../types/translation';

interface JobStatusProps {
    jobId: string;
    initialStatus?: JobStatusResponse;
    onJobComplete?: (job: JobStatusResponse) => void;
}

export const JobStatus: React.FC<JobStatusProps> = ({ jobId, initialStatus, onJobComplete }) => {
    const [job, setJob] = useState<JobStatusResponse | null>(initialStatus || null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState(true);
    const [downloadingFile, setDownloadingFile] = useState<string | null>(null);

    const fetchJobStatus = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await translationService.getJobStatus(jobId);
            setJob(response);
            
            if (response.status === 'completed' && onJobComplete) {
                onJobComplete(response);
            }
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch job status';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!initialStatus) {
            fetchJobStatus();
        }
    }, [jobId, initialStatus]);

    // Auto-refresh for active jobs
    useEffect(() => {
        if (!job || job.status === 'completed' || job.status === 'failed') {
            return;
        }

        const interval = setInterval(() => {
            fetchJobStatus();
        }, 3000); // Refresh every 3 seconds

        return () => clearInterval(interval);
    }, [job?.status]);

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
            case 'preprocessing_audio_en': return 'Preprocessing Audio';
            case 'transcribing_en': return 'Transcribing';
            case 'formatting_text_en': return 'Formatting Text';
            case 'translating_chunks_jp': return 'Translating';
            case 'merging_chunks_jp': return 'Merging Translation';
            case 'cleaning_text_jp': return 'Cleaning Text';
            case 'generating_audio_jp': return 'Generating Audio';
            case 'completed': return 'Completed';
            case 'failed': return 'Failed';
            default: return status;
        }
    };

    const handleDownload = async (fileType: 'english_transcript' | 'japanese_transcript' | 'japanese_audio') => {
        if (!job) return;

        setDownloadingFile(fileType);
        try {
            await translationService.downloadAndSaveFile(job.job_id, fileType);
        } catch (err: any) {
            setError(`Failed to download ${fileType}: ${err.message}`);
        } finally {
            setDownloadingFile(null);
        }
    };

    const getFileTypeLabel = (fileType: string): string => {
        switch (fileType) {
            case 'english_transcript': return 'English Transcript';
            case 'japanese_transcript': return 'Japanese Transcript';
            case 'japanese_audio': return 'Japanese Audio';
            default: return fileType;
        }
    };

    if (!job) {
        return (
            <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Typography variant="h6">Job Status</Typography>
                    <Button onClick={fetchJobStatus} disabled={loading} startIcon={<RefreshIcon />}>
                        {loading ? 'Loading...' : 'Refresh'}
                    </Button>
                </Box>
                {error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        {error}
                    </Alert>
                )}
            </Paper>
        );
    }

    return (
        <Paper elevation={2} sx={{ p: 3, mb: 2 }}>
            {/* Job Header */}
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="h6">
                        Translation Job
                    </Typography>
                    <Chip 
                        label={getStatusText(job.status)} 
                        color={getStatusColor(job.status)}
                        size="small"
                    />
                </Box>
                <Box display="flex" gap={1}>
                    <Button 
                        onClick={fetchJobStatus} 
                        disabled={loading}
                        startIcon={<RefreshIcon />}
                        size="small"
                    >
                        Refresh
                    </Button>
                    <Button
                        onClick={() => setExpanded(!expanded)}
                        startIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        size="small"
                    >
                        {expanded ? 'Collapse' : 'Expand'}
                    </Button>
                </Box>
            </Box>

            <Collapse in={expanded}>
                {/* Job ID */}
                <Typography variant="body2" color="textSecondary" gutterBottom>
                    Job ID: {job.job_id}
                </Typography>

                {/* Progress Bar */}
                <Box sx={{ mb: 2 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">{job.message}</Typography>
                        <Typography variant="body2" color="textSecondary">
                            {job.progress}%
                        </Typography>
                    </Box>
                    <LinearProgress 
                        variant="determinate" 
                        value={job.progress} 
                        sx={{ height: 8, borderRadius: 4 }}
                    />
                </Box>

                {/* Error Message */}
                {job.error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {job.error}
                    </Alert>
                )}

                {/* Download Files */}
                {job.files && job.files.length > 0 && (
                    <Box>
                        <Typography variant="subtitle2" gutterBottom>
                            Available Files:
                        </Typography>
                        <List dense>
                            {job.files.map((file: TranslationFile) => (
                                <ListItem key={file.type}>
                                    <ListItemText 
                                        primary={getFileTypeLabel(file.type)}
                                        secondary={file.available ? 'Ready for download' : 'Not available yet'}
                                    />
                                    <ListItemSecondaryAction>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            startIcon={<DownloadIcon />}
                                            onClick={() => handleDownload(file.type)}
                                            disabled={!file.available || downloadingFile === file.type}
                                        >
                                            {downloadingFile === file.type ? 'Downloading...' : 'Download'}
                                        </Button>
                                    </ListItemSecondaryAction>
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}
            </Collapse>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                    {error}
                </Alert>
            )}
        </Paper>
    );
};