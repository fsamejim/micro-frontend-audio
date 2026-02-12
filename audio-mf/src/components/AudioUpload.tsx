import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
    Box,
    Button,
    Paper,
    Typography,
    LinearProgress,
    Alert,
    IconButton,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Slider,
    Link,
    Divider,
    FormControlLabel,
    Checkbox
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material/Select';
import {
    CloudUpload as UploadIcon,
    Delete as DeleteIcon,
    AudioFile as AudioIcon,
    Replay as ReplayIcon,
    Close as CloseIcon,
    PlayArrow as PlayIcon,
    Stop as StopIcon
} from '@mui/icons-material';
import { translationService } from '../services/translationService';
import type { JobStatusResponse, Voice } from '../types/translation';
import { useAuth } from '../contexts/AuthContext';

interface AudioUploadProps {
    onJobCreated?: (job: JobStatusResponse) => void;
    regenerateJobId?: string | null;
    onCancelRegenerate?: () => void;
    onRegenerationStarted?: () => void;
}

type LanguageDirection = 'EN_JP' | 'JP_EN';

export const AudioUpload: React.FC<AudioUploadProps> = ({
    onJobCreated,
    regenerateJobId,
    onCancelRegenerate,
    onRegenerationStarted
}) => {
    const { user } = useAuth();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [languageDirection, setLanguageDirection] = useState<LanguageDirection>('EN_JP');
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Regeneration mode state
    const [speakers, setSpeakers] = useState<string[]>([]);
    const [availableVoices, setAvailableVoices] = useState<Voice[]>([]);
    const [voiceMappings, setVoiceMappings] = useState<Record<string, string>>({});
    const [speakingRate, setSpeakingRate] = useState<number>(1.2);
    const [loadingVoices, setLoadingVoices] = useState(false);
    const [regenerating, setRegenerating] = useState(false);
    const [voicesDocUrl, setVoicesDocUrl] = useState<string>('');
    const [targetLanguage, setTargetLanguage] = useState<string>('ja');
    const [transcriptSource, setTranscriptSource] = useState<'target' | 'source'>('target');
    const [sourceLanguage, setSourceLanguage] = useState<string>('en');
    const [voiceLanguage, setVoiceLanguage] = useState<string>('ja'); // Can differ from transcript for accent mixing
    const [accentMixingEnabled, setAccentMixingEnabled] = useState<boolean>(false);

    // Voice sample playback state (track by speaker, not voice name)
    const [playingSpeaker, setPlayingSpeaker] = useState<string | null>(null);
    const [loadingSpeaker, setLoadingSpeaker] = useState<string | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const isPlayingRef = useRef<boolean>(false); // Prevent double-clicks

    // Load speakers and voices when entering regeneration mode
    useEffect(() => {
        if (regenerateJobId) {
            loadRegenerationData();
        } else {
            // Reset regeneration state when exiting
            setSpeakers([]);
            setAvailableVoices([]);
            setVoiceMappings({});
            setSpeakingRate(1.2);
            setTargetLanguage('ja');
            setSourceLanguage('en');
            setTranscriptSource('target');
            setVoiceLanguage('ja');
            setAccentMixingEnabled(false);
        }
    }, [regenerateJobId]);

    const loadRegenerationData = async () => {
        if (!regenerateJobId) return;

        setLoadingVoices(true);
        setError(null);

        try {
            // Get speakers and target language
            console.log(`Loading regeneration data for job: ${regenerateJobId}`);
            const speakersResponse = await translationService.getJobSpeakers(regenerateJobId);
            const jobTargetLanguage = speakersResponse.target_language || 'ja';

            const jobSourceLanguage = speakersResponse.source_language || 'en';

            console.log(`Job speakers response:`, speakersResponse);
            console.log(`Job target language: ${jobTargetLanguage}, source language: ${jobSourceLanguage}`);

            setSpeakers(speakersResponse.speakers);
            setTargetLanguage(jobTargetLanguage);
            setSourceLanguage(jobSourceLanguage);
            setVoiceLanguage(jobTargetLanguage); // Default voice language matches target transcript

            // Initialize voice mappings with empty values (will use defaults)
            const initialMappings: Record<string, string> = {};
            speakersResponse.speakers.forEach(speaker => {
                initialMappings[speaker] = '';
            });
            setVoiceMappings(initialMappings);

            // Load voices for the target language
            console.log(`Loading voices for language: ${jobTargetLanguage}`);
            const voicesResponse = await translationService.getAvailableVoices(jobTargetLanguage);
            console.log(`Loaded ${voicesResponse.voices.length} voices:`, voicesResponse.voices.slice(0, 5));
            setAvailableVoices(voicesResponse.voices);
            setVoicesDocUrl(voicesResponse.documentation_url);
        } catch (err: any) {
            console.error('Failed to load regeneration data:', err);
            setError(`Failed to load regeneration data: ${err.message}`);
        } finally {
            setLoadingVoices(false);
        }
    };

    // Function to load voices for a specific language
    const loadVoicesForLanguage = async (lang: string) => {
        console.log(`loadVoicesForLanguage called with lang: ${lang}`);
        setLoadingVoices(true);
        try {
            const voicesResponse = await translationService.getAvailableVoices(lang);
            console.log(`Loaded ${voicesResponse.voices.length} voices for language ${lang}:`, voicesResponse.voices.slice(0, 5));
            setAvailableVoices(voicesResponse.voices);
            setVoicesDocUrl(voicesResponse.documentation_url);

            // Reset voice mappings when language changes
            const resetMappings: Record<string, string> = {};
            speakers.forEach(speaker => {
                resetMappings[speaker] = '';
            });
            setVoiceMappings(resetMappings);
        } catch (err: any) {
            console.error(`Failed to load voices for ${lang}:`, err);
            setError(`Failed to load voices: ${err.message}`);
        } finally {
            setLoadingVoices(false);
        }
    };

    // Handle transcript source change
    const handleTranscriptSourceChange = async (event: SelectChangeEvent) => {
        const newSource = event.target.value as 'target' | 'source';
        console.log(`Transcript source changed to: ${newSource}`);
        setTranscriptSource(newSource);

        // Determine the natural voice language for this transcript
        const transcriptLang = newSource === 'target' ? targetLanguage : sourceLanguage;

        // Auto-update voice language to match transcript (unless accent mixing is enabled)
        if (!accentMixingEnabled) {
            setVoiceLanguage(transcriptLang);
            await loadVoicesForLanguage(transcriptLang);
        }
        // If accent mixing is enabled, keep current voiceLanguage (no voice list reload needed)
    };

    // Handle voice language change (advanced option for accent mixing)
    const handleVoiceLanguageChange = async (event: SelectChangeEvent) => {
        const newLang = event.target.value;
        console.log(`Voice language changed to: ${newLang} (accent mixing mode)`);
        setVoiceLanguage(newLang);
        await loadVoicesForLanguage(newLang);
    };

    const handleVoiceChange = (speaker: string, voiceName: string) => {
        setVoiceMappings(prev => ({
            ...prev,
            [speaker]: voiceName
        }));
    };

    const handleSpeakingRateChange = (_event: Event, newValue: number | number[]) => {
        setSpeakingRate(newValue as number);
    };

    const handleRegenerate = async () => {
        if (!regenerateJobId) return;

        // Stop any playing sample before regenerating
        stopVoiceSample();

        setRegenerating(true);
        setError(null);
        setSuccess(null);

        try {
            // Filter out empty voice mappings (will use defaults)
            const filteredMappings: Record<string, string> = {};
            Object.entries(voiceMappings).forEach(([speaker, voice]) => {
                if (voice) {
                    filteredMappings[speaker] = voice;
                }
            });

            const response = await translationService.regenerateAudio(
                regenerateJobId,
                filteredMappings,
                speakingRate,
                transcriptSource
            );

            setSuccess(`${response.message}`);

            if (onRegenerationStarted) {
                onRegenerationStarted();
            }
        } catch (err: any) {
            setError(`Regeneration failed: ${err.response?.data?.detail || err.message}`);
        } finally {
            setRegenerating(false);
        }
    };

    // Voice sample playback functions - with double-click prevention
    const playVoiceSample = async (speaker: string, voiceName: string) => {
        // Prevent double-clicks
        if (isPlayingRef.current) {
            console.log('Play already in progress, ignoring');
            return;
        }

        // Stop any currently playing sample first
        stopVoiceSample();

        // Set lock immediately
        isPlayingRef.current = true;
        setLoadingSpeaker(speaker);

        try {
            const sampleUrl = translationService.getVoiceSampleUrl(voiceName, voiceLanguage);
            console.log(`Playing voice sample: ${voiceName}, language: ${voiceLanguage}, URL: ${sampleUrl}`);

            // Create new audio element
            const audio = new Audio();
            audioRef.current = audio;

            // Set up ended handler
            audio.addEventListener('ended', () => {
                console.log('Audio playback ended');
                isPlayingRef.current = false;
                setPlayingSpeaker(null);
            }, { once: true });

            // Set up error handler
            audio.addEventListener('error', (e) => {
                console.error('Audio error event:', e);
                isPlayingRef.current = false;
                setPlayingSpeaker(null);
                setLoadingSpeaker(null);
            }, { once: true });

            // Set source and play directly
            audio.src = sampleUrl;

            await audio.play();
            setLoadingSpeaker(null);
            setPlayingSpeaker(speaker);
        } catch (err: any) {
            console.error('Audio play error:', err);
            setError(`Failed to play sample for ${voiceName}`);
            isPlayingRef.current = false;
            setLoadingSpeaker(null);
            setPlayingSpeaker(null);
        }
    };

    const stopVoiceSample = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.src = '';
            audioRef.current = null;
        }
        isPlayingRef.current = false;
        setPlayingSpeaker(null);
        setLoadingSpeaker(null);
    };

    // Cleanup audio on unmount or when leaving regeneration mode
    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
        };
    }, [regenerateJobId]);

    const handleLanguageChange = (event: SelectChangeEvent) => {
        setLanguageDirection(event.target.value as LanguageDirection);
    };

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
            // Parse language direction into source and target
            const sourceLanguage = languageDirection === 'EN_JP' ? 'en' : 'ja';
            const targetLanguage = languageDirection === 'EN_JP' ? 'ja' : 'en';

            const response = await translationService.uploadAudio(selectedFile, user.id, sourceLanguage, targetLanguage);
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

    // Regeneration Mode UI
    if (regenerateJobId) {
        return (
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                {/* Header with close button */}
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                        <ReplayIcon color="secondary" />
                        <Typography variant="h6">
                            Re-Generate Audio
                        </Typography>
                    </Box>
                    {onCancelRegenerate && (
                        <IconButton onClick={onCancelRegenerate} size="small">
                            <CloseIcon />
                        </IconButton>
                    )}
                </Box>

                <Typography variant="body2" color="textSecondary" gutterBottom>
                    Job ID: {regenerateJobId}
                </Typography>

                <Divider sx={{ my: 2 }} />

                {loadingVoices ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                        <LinearProgress sx={{ mb: 2 }} />
                        <Typography>Loading voice options...</Typography>
                    </Box>
                ) : (
                    <>
                        {/* Transcript Source Selector */}
                        <Box sx={{ mb: 2 }}>
                            <FormControl fullWidth size="small">
                                <InputLabel id="transcript-source-label">Transcript to Use</InputLabel>
                                <Select
                                    labelId="transcript-source-label"
                                    value={transcriptSource}
                                    label="Transcript to Use"
                                    onChange={handleTranscriptSourceChange}
                                    disabled={regenerating || loadingVoices}
                                >
                                    <MenuItem value="target">
                                        Target Transcript ({targetLanguage === 'ja' ? 'Japanese' : 'English'})
                                    </MenuItem>
                                    <MenuItem value="source">
                                        Source Transcript ({sourceLanguage === 'ja' ? 'Japanese' : 'English'})
                                    </MenuItem>
                                </Select>
                            </FormControl>
                        </Box>

                        {/* Accent Mixing Toggle */}
                        <Box sx={{ mb: 2 }}>
                            <FormControlLabel
                                control={
                                    <Checkbox
                                        checked={accentMixingEnabled}
                                        onChange={(e) => {
                                            setAccentMixingEnabled(e.target.checked);
                                            // Reset voice language to match transcript when disabling
                                            if (!e.target.checked) {
                                                const transcriptLang = transcriptSource === 'target' ? targetLanguage : sourceLanguage;
                                                setVoiceLanguage(transcriptLang);
                                                loadVoicesForLanguage(transcriptLang);
                                            }
                                        }}
                                        size="small"
                                        disabled={regenerating || loadingVoices}
                                    />
                                }
                                label={
                                    <Typography variant="body2" color="textSecondary">
                                        Enable accent mixing
                                    </Typography>
                                }
                            />
                        </Box>

                        {/* Voice Language Selector (only shown when accent mixing is enabled) */}
                        {accentMixingEnabled && (
                            <Box sx={{ mb: 2 }}>
                                <FormControl fullWidth size="small">
                                    <InputLabel id="voice-language-label">Voice Language</InputLabel>
                                    <Select
                                        labelId="voice-language-label"
                                        value={voiceLanguage}
                                        label="Voice Language"
                                        onChange={handleVoiceLanguageChange}
                                        disabled={regenerating || loadingVoices}
                                    >
                                        <MenuItem value="ja">Japanese</MenuItem>
                                        <MenuItem value="en">English</MenuItem>
                                    </Select>
                                </FormControl>
                                <Typography variant="caption" color="textSecondary">
                                    Use a different voice language for accented speech (e.g., Japanese voice speaking English text).
                                </Typography>
                            </Box>
                        )}

                        {/* Voice Mappings */}
                        <Typography variant="subtitle2" gutterBottom>
                            Voice Mappings:
                        </Typography>
                        <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 2 }}>
                            Select a voice for each speaker, or leave empty to use defaults.
                        </Typography>

                        {speakers.map(speaker => {
                            const selectedVoice = voiceMappings[speaker] || '';
                            const isPlaying = playingSpeaker === speaker;
                            const isLoading = loadingSpeaker === speaker;

                            return (
                                <Box key={speaker} sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <FormControl sx={{ flex: 1 }} size="small">
                                        <InputLabel id={`voice-${speaker}-label`}>{speaker}</InputLabel>
                                        <Select
                                            labelId={`voice-${speaker}-label`}
                                            value={selectedVoice}
                                            label={speaker}
                                            onChange={(e) => handleVoiceChange(speaker, e.target.value)}
                                            disabled={regenerating}
                                        >
                                            <MenuItem value="">
                                                <em>Use default voice</em>
                                            </MenuItem>
                                            {availableVoices
                                                .filter(voice => {
                                                    // Filter out Chirp3-HD voices when accent mixing with Japanese voice
                                                    if (accentMixingEnabled && voiceLanguage === 'ja' && voice.name.includes('Chirp3-HD')) {
                                                        return false;
                                                    }
                                                    return true;
                                                })
                                                .map(voice => (
                                                <MenuItem key={voice.name} value={voice.name}>
                                                    {voice.name} ({voice.gender})
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                    {/* Play Sample Button */}
                                    <IconButton
                                        size="small"
                                        color={isPlaying ? 'secondary' : 'primary'}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            e.preventDefault();
                                            console.log(`Play button clicked for ${speaker}, voice: ${selectedVoice}, isPlaying: ${isPlaying}`);
                                            if (isPlaying) {
                                                stopVoiceSample();
                                            } else if (selectedVoice) {
                                                playVoiceSample(speaker, selectedVoice);
                                            }
                                        }}
                                        disabled={!selectedVoice || regenerating || isLoading}
                                        title={selectedVoice ? (isPlaying ? 'Stop sample' : 'Play sample') : 'Select a voice first'}
                                        sx={{
                                            border: '1px solid',
                                            borderColor: isPlaying ? 'secondary.main' : 'primary.main',
                                            opacity: selectedVoice ? 1 : 0.5
                                        }}
                                    >
                                        {isLoading ? (
                                            <Typography variant="caption" sx={{ fontSize: 10, px: 0.5 }}>...</Typography>
                                        ) : isPlaying ? (
                                            <StopIcon fontSize="small" />
                                        ) : (
                                            <PlayIcon fontSize="small" />
                                        )}
                                    </IconButton>
                                </Box>
                            );
                        })}

                        <Divider sx={{ my: 2 }} />

                        {/* Speaking Rate Slider */}
                        <Typography variant="subtitle2" gutterBottom>
                            Speaking Rate: {speakingRate.toFixed(1)}x
                        </Typography>
                        <Box sx={{ px: 2, mb: 3 }}>
                            <Slider
                                value={speakingRate}
                                onChange={handleSpeakingRateChange}
                                min={0.5}
                                max={2.0}
                                step={0.1}
                                marks={[
                                    { value: 0.5, label: '0.5x' },
                                    { value: 1.0, label: '1.0x' },
                                    { value: 1.5, label: '1.5x' },
                                    { value: 2.0, label: '2.0x' }
                                ]}
                                disabled={regenerating}
                            />
                        </Box>

                        {/* Documentation Link */}
                        {voicesDocUrl && (
                            <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 2 }}>
                                Available voices:{' '}
                                <Link href={voicesDocUrl} target="_blank" rel="noopener noreferrer">
                                    {voicesDocUrl}
                                </Link>
                            </Typography>
                        )}

                        {/* Generate Button */}
                        <Box display="flex" justifyContent="center" mt={3}>
                            <Button
                                variant="contained"
                                color="secondary"
                                size="large"
                                onClick={handleRegenerate}
                                disabled={regenerating}
                                startIcon={<ReplayIcon />}
                                sx={{ minWidth: 200 }}
                            >
                                {regenerating ? 'Generating...' : 'Generate New Audio'}
                            </Button>
                        </Box>

                        {/* Progress */}
                        {regenerating && (
                            <Box sx={{ mt: 2 }}>
                                <LinearProgress color="secondary" />
                                <Typography variant="body2" textAlign="center" sx={{ mt: 1 }}>
                                    Generating audio with custom voices...
                                </Typography>
                            </Box>
                        )}
                    </>
                )}

                {/* Error Alert */}
                {error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                        {error}
                    </Alert>
                )}

                {/* Success Alert */}
                {success && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                        {success}
                    </Alert>
                )}
            </Paper>
        );
    }

    // Normal Upload Mode UI
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
                    Supported formats: MP3, WAV, M4A, FLAC (max 300MB)
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

            {/* Language Direction Selector */}
            <Box sx={{ mb: 2 }}>
                <FormControl fullWidth size="small">
                    <InputLabel id="language-direction-label">Translation Direction</InputLabel>
                    <Select
                        labelId="language-direction-label"
                        id="language-direction"
                        value={languageDirection}
                        label="Translation Direction"
                        onChange={handleLanguageChange}
                        disabled={uploading}
                    >
                        <MenuItem value="EN_JP">English → Japanese</MenuItem>
                        <MenuItem value="JP_EN">Japanese → English</MenuItem>
                    </Select>
                </FormControl>
            </Box>

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