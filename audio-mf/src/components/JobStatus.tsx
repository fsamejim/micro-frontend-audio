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
    ExpandLess as ExpandLessIcon,
    Replay as ReplayIcon
} from '@mui/icons-material';
import { translationService } from '../services/translationService';
import type { JobStatusResponse, TranslationFile, AudioVersion } from '../types/translation';

interface JobStatusProps {
    jobId: string;
    initialStatus?: JobStatusResponse;
    onJobComplete?: (job: JobStatusResponse) => void;
    onRegenerateAudio?: (jobId: string) => void;
}

export const JobStatus: React.FC<JobStatusProps> = ({ jobId, initialStatus, onJobComplete, onRegenerateAudio }) => {
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
            
            if (response.status === 'COMPLETED' && onJobComplete) {
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
        // Always fetch fresh data on mount to ensure files array is populated
        fetchJobStatus();
    }, [jobId]);

    // Check if regeneration is in progress (message contains "Regenerating" or "regenerating")
    const isRegenerating = job?.message?.toLowerCase().includes('regenerating');

    // Auto-refresh for active jobs or during regeneration
    useEffect(() => {
        // Continue polling if job is in progress OR if regeneration is happening
        const shouldPoll = job && (
            (job.status !== 'COMPLETED' && job.status !== 'FAILED') ||
            isRegenerating
        );

        if (!shouldPoll) {
            return;
        }

        const interval = setInterval(() => {
            fetchJobStatus();
        }, 3000); // Refresh every 3 seconds

        return () => clearInterval(interval);
    }, [job?.status, isRegenerating]);

    const getStatusColor = (status: string): 'primary' | 'secondary' | 'success' | 'error' | 'warning' => {
        switch (status) {
            case 'COMPLETED': return 'success';
            case 'FAILED': return 'error';
            case 'UPLOADED': return 'primary';
            default: return 'warning';
        }
    };

    const getStatusText = (status: string): string => {
        switch (status) {
            case 'UPLOADED': return 'Uploaded';
            case 'PREPROCESSING_AUDIO': return 'Preprocessing Audio';
            case 'TRANSCRIBING_SOURCE': return 'Transcribing';
            case 'FORMATTING_SOURCE_TEXT': return 'Formatting Text';
            case 'TRANSLATING_TO_TARGET': return 'Translating';
            case 'MERGING_TARGET_CHUNKS': return 'Merging Translation';
            case 'CLEANING_TARGET_TEXT': return 'Cleaning Text';
            case 'GENERATING_TARGET_AUDIO': return 'Generating Audio';
            case 'COMPLETED': return 'Completed';
            case 'FAILED': return 'Failed';
            default: return status;
        }
    };

    const handleDownload = async (fileType: string) => {
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

    const handleRegenerateClick = () => {
        if (job && onRegenerateAudio) {
            onRegenerateAudio(job.job_id);
        }
    };

    const getFileTypeLabel = (fileType: string): string => {
        switch (fileType) {
            case 'source_transcript': return 'Source Transcript';
            case 'target_transcript': return 'Target Transcript';
            case 'target_audio': return 'Target Audio';
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
                    {/* Show additional progress indicator during regeneration */}
                    {isRegenerating && (
                        <Box sx={{ mt: 1 }}>
                            <LinearProgress color="secondary" />
                            <Typography variant="caption" color="secondary" sx={{ mt: 0.5, display: 'block' }}>
                                Audio regeneration in progress... Please wait.
                            </Typography>
                        </Box>
                    )}
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
                            {/* Show transcript files (non-audio) */}
                            {job.files
                                .filter((file: TranslationFile) => !file.type.includes('audio'))
                                .map((file: TranslationFile) => (
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

                            {/* Show audio versions */}
                            {job.audio_versions && job.audio_versions.length > 0 && (
                                <>
                                    {job.audio_versions.map((version: AudioVersion) => {
                                        // Build voice info string
                                        const voiceMappings = version.voice_mappings || {};
                                        const voiceEntries = Object.entries(voiceMappings);
                                        const voiceInfo = voiceEntries.length > 0
                                            ? voiceEntries.map(([speaker, voice]) => `${speaker}: ${voice}`).join(', ')
                                            : 'Default voices';

                                        return (
                                            <ListItem key={version.type} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                                                <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <ListItemText
                                                        primary={`Target Audio (v${version.version})`}
                                                        secondary={
                                                            version.available
                                                                ? `Rate: ${version.speaking_rate}x`
                                                                : 'Not available yet'
                                                        }
                                                    />
                                                    <Button
                                                        size="small"
                                                        variant="outlined"
                                                        startIcon={<DownloadIcon />}
                                                        onClick={() => handleDownload(version.type)}
                                                        disabled={!version.available || downloadingFile === version.type}
                                                    >
                                                        {downloadingFile === version.type ? 'Downloading...' : 'Download'}
                                                    </Button>
                                                </Box>
                                                {version.available && (
                                                    <Typography variant="caption" color="textSecondary" sx={{ pl: 2, mt: 0.5 }}>
                                                        Voices: {voiceInfo}
                                                    </Typography>
                                                )}
                                            </ListItem>
                                        );
                                    })}
                                </>
                            )}
                        </List>
                    </Box>
                )}

                {/* Re-Generate Audio Button (only for completed jobs) */}
                {job.status === 'COMPLETED' && onRegenerateAudio && (
                    <Box sx={{ mt: 2, textAlign: 'center' }}>
                        <Button
                            variant="contained"
                            color="secondary"
                            startIcon={<ReplayIcon />}
                            onClick={handleRegenerateClick}
                        >
                            Re-Generate Audio
                        </Button>
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