import React, { useState } from 'react';
import { Box, Typography, Button, Paper, Container, Tabs, Tab } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { AudioUpload } from './AudioUpload';
import { JobStatus } from './JobStatus';
import { JobHistory } from './JobHistory';
import { JobStatusResponse } from '../types/translation';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function TabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ pt: 3 }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

export const Dashboard: React.FC = () => {
    const { user, logout, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState(0);
    const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
    const [viewingJobId, setViewingJobId] = useState<string | null>(null);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setActiveTab(newValue);
    };

    const handleJobCreated = (job: JobStatusResponse) => {
        setActiveJob(job);
        setActiveTab(1); // Switch to Active Job tab
    };

    const handleViewJob = (jobId: string) => {
        setViewingJobId(jobId);
        setActiveTab(1); // Switch to Active Job tab
    };

    const handleJobComplete = (job: JobStatusResponse) => {
        // Job completed, could show notification or update history
        console.log('Job completed:', job.job_id);
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            {/* Header */}
            <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                        <Typography variant="h4" component="h1" gutterBottom>
                            Audio Translation Dashboard
                        </Typography>
                        <Typography variant="h6" color="text.secondary">
                            Welcome{user?.username ? `, ${user.username}` : ''}!
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            Debug: User ID = {user?.id || 'NOT LOADED'}, Auth = {JSON.stringify({isAuthenticated, hasToken: !!localStorage.getItem('token')})}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Upload audio files to translate from English to Japanese
                        </Typography>
                    </Box>
                    <Button 
                        variant="outlined" 
                        color="secondary" 
                        onClick={handleLogout}
                        sx={{ minWidth: '100px' }}
                    >
                        Logout
                    </Button>
                </Box>
            </Paper>

            {/* Navigation Tabs */}
            <Paper elevation={2} sx={{ mb: 3 }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={activeTab} onChange={handleTabChange} aria-label="dashboard tabs">
                        <Tab label="Upload Audio" />
                        <Tab label="Active Job" />
                        <Tab label="Job History" />
                    </Tabs>
                </Box>

                {/* Upload Tab */}
                <TabPanel value={activeTab} index={0}>
                    <AudioUpload onJobCreated={handleJobCreated} />
                </TabPanel>

                {/* Active Job Tab */}
                <TabPanel value={activeTab} index={1}>
                    {activeJob || viewingJobId ? (
                        <JobStatus 
                            jobId={viewingJobId || activeJob?.job_id || ''} 
                            initialStatus={activeJob || undefined}
                            onJobComplete={handleJobComplete}
                        />
                    ) : (
                        <Box textAlign="center" py={6}>
                            <Typography variant="h6" color="textSecondary" gutterBottom>
                                No Active Job
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Upload an audio file to start a translation job.
                            </Typography>
                            <Button 
                                variant="contained" 
                                sx={{ mt: 2 }}
                                onClick={() => setActiveTab(0)}
                            >
                                Upload Audio
                            </Button>
                        </Box>
                    )}
                </TabPanel>

                {/* History Tab */}
                <TabPanel value={activeTab} index={2}>
                    <JobHistory onViewJob={handleViewJob} />
                </TabPanel>
            </Paper>

            {/* Info Section */}
            <Paper elevation={1} sx={{ p: 3, backgroundColor: '#f8f9fa' }}>
                <Typography variant="h6" gutterBottom>
                    How it works
                </Typography>
                <Box component="ol" sx={{ pl: 2 }}>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        <strong>Upload:</strong> Drag and drop or select an audio file (MP3, WAV, M4A, FLAC)
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        <strong>Processing:</strong> The system will transcribe the English audio and translate it to Japanese
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        <strong>Results:</strong> Download the English transcript, Japanese translation, and Japanese audio
                    </Typography>
                </Box>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                    Processing time varies depending on file length. You can track progress in the Active Job tab.
                </Typography>
            </Paper>
        </Container>
    );
};