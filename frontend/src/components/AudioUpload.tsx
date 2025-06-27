import React, { useState, useRef, useCallback } from 'react';
import {
    Box,
    Button,
    Paper,
    Typography,
    LinearProgress,
    Alert,
    Chip,
    IconButton,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction
} from '@mui/material';
import {
    CloudUpload as UploadIcon,
    Delete as DeleteIcon,
    Download as DownloadIcon,
    AudioFile as AudioIcon
} from '@mui/icons-material';
import { translationService } from '../services/translationService';
import { TranslationJob, JobStatusResponse } from '../types/translation';
import { useAuth } from '../contexts/AuthContext';

interface AudioUploadProps {
    onJobCreated?: (job: JobStatusResponse) => void;
}

export const AudioUpload: React.FC<AudioUploadProps> = ({ onJobCreated }) => {
    const { user } = useAuth();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    }, []);

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFileSelection(files[0]);
        }
    };

    const handleFileSelection = (file: File) => {
        setError(null);
        setSuccess(null);

        const validation = translationService.validateAudioFile(file);
        if (!validation.isValid) {
            setError(validation.error || 'Invalid file');
            return;
        }

        setSelectedFile(file);
    };

    const handleUpload = async () => {
        console.log('Upload clicked - selectedFile:', selectedFile?.name, 'user:', user);
        
        if (!selectedFile || !user) {
            console.log('Upload failed - selectedFile:', !!selectedFile, 'user:', !!user);
            setError('Please select a file and ensure you are logged in');
            return;
        }

        setUploading(true);
        setError(null);
        setSuccess(null);

        try {
            const response = await translationService.uploadAudio(selectedFile, user.id);
            setSuccess(`Upload successful! Job ID: ${response.job_id}`);
            
            // Get initial job status
            const jobStatus = await translationService.getJobStatus(response.job_id);
            if (onJobCreated) {
                onJobCreated(jobStatus);
            }

            // Clear the selected file
            setSelectedFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }

        } catch (err: any) {
            console.error('Upload error:', err);
            console.error('Error response:', err.response?.data);
            
            let errorMessage = 'Upload failed';
            if (err.response?.status === 422) {
                errorMessage = `Upload validation failed: ${err.response?.data?.detail || 'Invalid request format'}`;
            } else if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            } else if (err.message) {
                errorMessage = err.message;
            }
            
            setError(errorMessage);
        } finally {
            setUploading(false);
        }
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
        setError(null);
        setSuccess(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
                Upload Audio File
            </Typography>

            {/* Drag and Drop Area */}
            <Box
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                sx={{
                    border: `2px dashed ${dragActive ? '#1976d2' : '#ccc'}`,
                    borderRadius: 2,
                    p: 4,
                    textAlign: 'center',
                    backgroundColor: dragActive ? '#f3f4f6' : '#fafafa',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    mb: 2,
                    '&:hover': {
                        borderColor: '#1976d2',
                        backgroundColor: '#f3f4f6'
                    }
                }}
                onClick={() => fileInputRef.current?.click()}
            >
                <UploadIcon sx={{ fontSize: 48, color: '#666', mb: 2 }} />
                <Typography variant="h6" color="textSecondary" gutterBottom>
                    {dragActive ? 'Drop your audio file here' : 'Drag and drop your audio file here'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                    or click to browse files
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }} color="textSecondary">
                    Supported formats: MP3, WAV, M4A, FLAC (max 100MB)
                </Typography>
            </Box>

            {/* Hidden File Input */}
            <input
                ref={fileInputRef}
                type="file"
                accept=".mp3,.wav,.m4a,.flac,audio/*"
                onChange={handleFileInputChange}
                style={{ display: 'none' }}
            />

            {/* Selected File Display */}
            {selectedFile && (
                <Box sx={{ mb: 2 }}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                        <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Box display="flex" alignItems="center">
                                <AudioIcon sx={{ mr: 1, color: '#1976d2' }} />
                                <Box>
                                    <Typography variant="body1" fontWeight="medium">
                                        {selectedFile.name}
                                    </Typography>
                                    <Typography variant="caption" color="textSecondary">
                                        {formatFileSize(selectedFile.size)}
                                    </Typography>
                                </Box>
                            </Box>
                            <IconButton 
                                onClick={handleRemoveFile} 
                                size="small"
                                disabled={uploading}
                            >
                                <DeleteIcon />
                            </IconButton>
                        </Box>
                    </Paper>
                </Box>
            )}

            {/* Upload Button */}
            <Box display="flex" justifyContent="center" mb={2}>
                <Button
                    variant="contained"
                    size="large"
                    onClick={handleUpload}
                    disabled={!selectedFile || uploading}
                    startIcon={<UploadIcon />}
                    sx={{ minWidth: 200 }}
                >
                    {uploading ? 'Uploading...' : 'Start Translation'}
                </Button>
            </Box>

            {/* Upload Progress */}
            {uploading && (
                <Box sx={{ mb: 2 }}>
                    <LinearProgress />
                    <Typography variant="body2" textAlign="center" sx={{ mt: 1 }}>
                        Uploading and starting translation process...
                    </Typography>
                </Box>
            )}

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Success Alert */}
            {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                    {success}
                </Alert>
            )}
        </Paper>
    );
};