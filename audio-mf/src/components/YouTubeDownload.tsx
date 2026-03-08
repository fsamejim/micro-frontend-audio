import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Typography,
    Paper,
    FormGroup,
    FormControlLabel,
    Checkbox,
    Alert,
    CircularProgress,
    Card,
    CardContent,
    Link,
    Divider,
} from '@mui/material';
import {
    Download as DownloadIcon,
    MusicNote as AudioIcon,
    Videocam as VideoIcon,
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = 'http://localhost:8001';

interface DownloadResult {
    success: boolean;
    file_path?: string;
    error?: string;
    format_id?: string;
    format_note?: string;
}

interface DownloadResponse {
    job_id: string;
    status: string;
    type: string;
    message: string;
    file_path?: string;
    format_id?: string;
    format_note?: string;
    audio?: DownloadResult;
    video?: DownloadResult;
}

export function YouTubeDownload() {
    const [url, setUrl] = useState('');
    const [downloadAudio, setDownloadAudio] = useState(true);
    const [downloadVideo, setDownloadVideo] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<DownloadResponse | null>(null);

    const handleDownload = async () => {
        if (!url.trim()) {
            setError('Please enter a YouTube URL');
            return;
        }

        if (!downloadAudio && !downloadVideo) {
            setError('Please select at least one download type');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        try {
            let downloadType: string;
            if (downloadAudio && downloadVideo) {
                downloadType = 'both';
            } else if (downloadAudio) {
                downloadType = 'audio';
            } else {
                downloadType = 'video';
            }

            const response = await axios.post<DownloadResponse>(`${API_URL}/youtube/download`, {
                url: url.trim(),
                type: downloadType,
            });

            setResult(response.data);
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.detail || err.message);
            } else {
                setError('An unexpected error occurred');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadFile = async (jobId: string, fileType: 'audio' | 'video') => {
        try {
            const response = await axios.get(`${API_URL}/youtube/download/${jobId}/${fileType}`, {
                responseType: 'blob',
            });

            const ext = fileType === 'audio' ? 'mp3' : 'mp4';
            const blob = new Blob([response.data]);
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `youtube_${fileType}_${jobId}.${ext}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(`Failed to download ${fileType}: ${err.message}`);
            }
        }
    };

    const isValidYouTubeUrl = (input: string): boolean => {
        const patterns = [
            /youtube\.com\/watch\?v=/,
            /youtu\.be\//,
            /youtube\.com\/embed\//,
            /youtube\.com\/v\//,
        ];
        return patterns.some(pattern => pattern.test(input));
    };

    return (
        <Box sx={{ maxWidth: 600, mx: 'auto', p: 2 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DownloadIcon /> YouTube Download
            </Typography>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Download audio (MP3) for translation input or video-only (MP4) for reference.
                Video downloads are optimized for Mac compatibility.
            </Typography>

            <Paper sx={{ p: 3, mb: 3 }}>
                <TextField
                    fullWidth
                    label="YouTube URL"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    error={!!url && !isValidYouTubeUrl(url)}
                    helperText={url && !isValidYouTubeUrl(url) ? 'Please enter a valid YouTube URL' : ''}
                    sx={{ mb: 2 }}
                />

                <FormGroup row sx={{ mb: 2 }}>
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={downloadAudio}
                                onChange={(e) => setDownloadAudio(e.target.checked)}
                            />
                        }
                        label={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <AudioIcon fontSize="small" /> Audio (MP3)
                            </Box>
                        }
                    />
                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={downloadVideo}
                                onChange={(e) => setDownloadVideo(e.target.checked)}
                            />
                        }
                        label={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <VideoIcon fontSize="small" /> Video-only (MP4)
                            </Box>
                        }
                    />
                </FormGroup>

                <Button
                    variant="contained"
                    onClick={handleDownload}
                    disabled={loading || !url.trim() || (!downloadAudio && !downloadVideo)}
                    startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
                    fullWidth
                >
                    {loading ? 'Downloading...' : 'Download'}
                </Button>
            </Paper>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {result && (
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            Download Complete
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            Job ID: {result.job_id}
                        </Typography>

                        <Divider sx={{ my: 2 }} />

                        {result.type === 'both' ? (
                            <>
                                {result.audio && (
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                            <AudioIcon fontSize="small" /> Audio
                                        </Typography>
                                        {result.audio.success ? (
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                                                <Typography variant="body2" color="success.main">
                                                    Ready
                                                </Typography>
                                                <Button
                                                    size="small"
                                                    variant="outlined"
                                                    onClick={() => handleDownloadFile(result.job_id, 'audio')}
                                                >
                                                    Download MP3
                                                </Button>
                                            </Box>
                                        ) : (
                                            <Typography variant="body2" color="error">
                                                Failed: {result.audio.error}
                                            </Typography>
                                        )}
                                    </Box>
                                )}

                                {result.video && (
                                    <Box>
                                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                            <VideoIcon fontSize="small" /> Video
                                        </Typography>
                                        {result.video.success ? (
                                            <Box sx={{ mt: 1 }}>
                                                <Typography variant="body2" color="text.secondary">
                                                    Format: {result.video.format_note}
                                                </Typography>
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                                                    <Typography variant="body2" color="success.main">
                                                        Ready
                                                    </Typography>
                                                    <Button
                                                        size="small"
                                                        variant="outlined"
                                                        onClick={() => handleDownloadFile(result.job_id, 'video')}
                                                    >
                                                        Download MP4
                                                    </Button>
                                                </Box>
                                            </Box>
                                        ) : (
                                            <Typography variant="body2" color="error">
                                                Failed: {result.video.error}
                                            </Typography>
                                        )}
                                    </Box>
                                )}
                            </>
                        ) : (
                            <Box>
                                {result.type === 'audio' && (
                                    <>
                                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                            <AudioIcon fontSize="small" /> Audio Ready
                                        </Typography>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            onClick={() => handleDownloadFile(result.job_id, 'audio')}
                                            sx={{ mt: 1 }}
                                        >
                                            Download MP3
                                        </Button>
                                    </>
                                )}

                                {result.type === 'video' && (
                                    <>
                                        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                            <VideoIcon fontSize="small" /> Video Ready
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Format: {result.format_note}
                                        </Typography>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            onClick={() => handleDownloadFile(result.job_id, 'video')}
                                            sx={{ mt: 1 }}
                                        >
                                            Download MP4
                                        </Button>
                                    </>
                                )}
                            </Box>
                        )}

                        <Divider sx={{ my: 2 }} />

                        <Typography variant="body2" color="text.secondary">
                            Tip: Downloaded audio can be used for translation via the{' '}
                            <Link href="/audio">Audio Upload</Link> page.
                        </Typography>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
}

export default YouTubeDownload;
