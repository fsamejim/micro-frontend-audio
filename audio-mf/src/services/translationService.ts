import axios from 'axios';
import type { UploadResponse, JobStatusResponse, UserJobsResponse, VoicesResponse, SpeakersResponse, RegenerateAudioResponse } from '../types/translation';

const TRANSLATION_API_URL = 'http://localhost:8001';

export const translationService = {
    // Upload audio file and start translation
    uploadAudio: async (
        file: File,
        userId: number,
        sourceLanguage: string = 'en',
        targetLanguage: string = 'ja'
    ): Promise<UploadResponse> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post(
            `${TRANSLATION_API_URL}/translation/upload?user_id=${userId}&source_language=${sourceLanguage}&target_language=${targetLanguage}`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );

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

    // Retry a failed translation job
    retryJob: async (jobId: string): Promise<{ job_id: string; status: string; message: string }> => {
        const response = await axios.post(`${TRANSLATION_API_URL}/translation/retry/${jobId}`);
        return response.data;
    },

    // Get available TTS voices for a language
    getAvailableVoices: async (languageCode: string = 'ja'): Promise<VoicesResponse> => {
        const response = await axios.get(`${TRANSLATION_API_URL}/translation/voices?language_code=${languageCode}`);
        return response.data;
    },

    // Get URL for voice sample audio
    getVoiceSampleUrl: (voiceName: string, languageCode: string = 'ja'): string => {
        return `${TRANSLATION_API_URL}/translation/voice-sample?voice_name=${encodeURIComponent(voiceName)}&language_code=${languageCode}`;
    },

    // Get speakers detected in a job's transcript
    getJobSpeakers: async (jobId: string): Promise<SpeakersResponse> => {
        const response = await axios.get(`${TRANSLATION_API_URL}/translation/speakers/${jobId}`);
        return response.data;
    },

    // Regenerate audio with custom voice mappings
    regenerateAudio: async (
        jobId: string,
        voiceMappings: Record<string, string>,
        speakingRate: number,
        transcriptSource: 'target' | 'source' = 'target'
    ): Promise<RegenerateAudioResponse> => {
        const response = await axios.post(`${TRANSLATION_API_URL}/translation/regenerate-audio/${jobId}`, {
            voice_mappings: voiceMappings,
            speaking_rate: speakingRate,
            transcript_source: transcriptSource
        });
        return response.data;
    },

    // Download a specific file from a completed job
    // fileType can be: source_transcript, target_transcript, target_audio, target_audio_v1, target_audio_v2, etc.
    downloadFile: async (jobId: string, fileType: string): Promise<Blob> => {
        const response = await axios.get(`${TRANSLATION_API_URL}/translation/download/${jobId}/${fileType}`, {
            responseType: 'blob',
        });
        return response.data;
    },

    // Helper function to download and save file
    // fileType can be: source_transcript, target_transcript, target_audio, target_audio_v1, target_audio_v2, etc.
    downloadAndSaveFile: async (jobId: string, fileType: string, filename?: string): Promise<void> => {
        try {
            const blob = await translationService.downloadFile(jobId, fileType);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;

            // Set filename based on file type if not provided
            if (!filename) {
                const extension = fileType.includes('audio') ? 'mp3' : 'txt';
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

    // Validate file type and size (supports both audio and text files)
    validateAudioFile: (file: File): { isValid: boolean; error?: string } => {
        const allowedAudioTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac', 'audio/mpeg'];
        const allowedAudioExtensions = ['.mp3', '.wav', '.m4a', '.flac'];
        const allowedTextTypes = ['text/plain'];
        const allowedTextExtensions = ['.txt'];
        const maxSize = 300 * 1024 * 1024; // 300MB

        // Check file size
        if (file.size > maxSize) {
            return { isValid: false, error: 'File size must be less than 300MB' };
        }

        // Check if it's a text file
        const isTextType = allowedTextTypes.includes(file.type);
        const isTextExtension = allowedTextExtensions.some(ext =>
            file.name.toLowerCase().endsWith(ext)
        );

        if (isTextType || isTextExtension) {
            return { isValid: true };
        }

        // Check if it's an audio file
        const isAudioType = allowedAudioTypes.includes(file.type);
        const isAudioExtension = allowedAudioExtensions.some(ext =>
            file.name.toLowerCase().endsWith(ext)
        );

        if (!isAudioType && !isAudioExtension) {
            return {
                isValid: false,
                error: 'Only audio files (mp3, wav, m4a, flac) or text files (.txt) are allowed'
            };
        }

        return { isValid: true };
    },

    // Convert text string to a File object for upload
    textToFile: (text: string, filename: string = 'input.txt'): File => {
        const blob = new Blob([text], { type: 'text/plain' });
        return new File([blob], filename, { type: 'text/plain' });
    },

    // Maximum characters for text input textarea
    TEXT_INPUT_MAX_CHARS: 50000
};