import axios from 'axios';
import { UploadResponse, JobStatusResponse, UserJobsResponse } from '../types/translation';

const TRANSLATION_API_URL = '';

export const translationService = {
    // Upload audio file and start translation
    uploadAudio: async (file: File, userId: number): Promise<UploadResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(`${TRANSLATION_API_URL}/translation/upload?user_id=${userId}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        return response.data;
    },

    // Get job status by job ID
    getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
        const response = await axios.get(`${TRANSLATION_API_URL}/translation/status/${jobId}`);
        return response.data;
    },

    // Get all jobs for a user
    getUserJobs: async (userId: number): Promise<UserJobsResponse> => {
        const response = await axios.get(`${TRANSLATION_API_URL}/translation/jobs/${userId}`);
        return response.data;
    },

    // Download a specific file from a completed job
    downloadFile: async (jobId: string, fileType: 'english_transcript' | 'japanese_transcript' | 'japanese_audio'): Promise<Blob> => {
        const response = await axios.get(`${TRANSLATION_API_URL}/translation/download/${jobId}/${fileType}`, {
            responseType: 'blob',
        });
        return response.data;
    },

    // Helper function to download and save file
    downloadAndSaveFile: async (jobId: string, fileType: 'english_transcript' | 'japanese_transcript' | 'japanese_audio', filename?: string): Promise<void> => {
        try {
            const blob = await translationService.downloadFile(jobId, fileType);
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            
            // Set filename based on file type if not provided
            if (!filename) {
                const extension = fileType === 'japanese_audio' ? 'mp3' : 'txt';
                filename = `${jobId}_${fileType}.${extension}`;
            }
            
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            
            // Cleanup
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading file:', error);
            throw new Error('Failed to download file');
        }
    },

    // Validate file type and size
    validateAudioFile: (file: File): { isValid: boolean; error?: string } => {
        const allowedTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac', 'audio/mpeg'];
        const allowedExtensions = ['.mp3', '.wav', '.m4a', '.flac'];
        const maxSize = 100 * 1024 * 1024; // 100MB

        // Check file size
        if (file.size > maxSize) {
            return { isValid: false, error: 'File size must be less than 100MB' };
        }

        // Check file type
        const isTypeValid = allowedTypes.includes(file.type);
        const isExtensionValid = allowedExtensions.some(ext => 
            file.name.toLowerCase().endsWith(ext)
        );

        if (!isTypeValid && !isExtensionValid) {
            return { 
                isValid: false, 
                error: 'Only audio files are allowed (mp3, wav, m4a, flac)' 
            };
        }

        return { isValid: true };
    }
};