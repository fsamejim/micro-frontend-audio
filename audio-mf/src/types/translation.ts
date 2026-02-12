export interface TranslationJob {
    job_id: string;
    original_filename: string;
    status: string;
    progress: number;
    message: string;
    error?: string;
    created_at?: string;
    completed_at?: string;
    files: TranslationFile[];
    audio_versions?: AudioVersion[];
}

export interface TranslationFile {
    type: 'source_transcript' | 'target_transcript' | 'target_audio' | string;
    available: boolean;
}

export interface AudioVersion {
    version: number;
    type: string;  // e.g., "target_audio_v1", "target_audio_v2"
    available: boolean;
    voice_mappings: Record<string, string>;
    speaking_rate: number;
}

export interface Voice {
    name: string;
    gender: 'MALE' | 'FEMALE' | 'NEUTRAL';
    language_codes: string[];
    natural_sample_rate_hertz: number;
}

export interface VoicesResponse {
    language_code: string;
    voices: Voice[];
    documentation_url: string;
}

export interface SpeakersResponse {
    job_id: string;
    speakers: string[];
    target_language: string;
    source_language: string;
}

export interface UploadResponse {
    job_id: string;
    status: string;
    message: string;
}

export interface JobStatusResponse {
    job_id: string;
    status: string;
    progress: number;
    message: string;
    error?: string;
    files: TranslationFile[];
    audio_versions: AudioVersion[];
}

export interface UserJobsResponse {
    jobs: TranslationJob[];
}

export interface RegenerateAudioResponse {
    job_id: string;
    status: string;
    version: number;
    message: string;
}

export type JobStatus =
    | 'UPLOADED'
    | 'PREPROCESSING_AUDIO'
    | 'TRANSCRIBING_SOURCE'
    | 'FORMATTING_SOURCE_TEXT'
    | 'TRANSLATING_TO_TARGET'
    | 'MERGING_TARGET_CHUNKS'
    | 'CLEANING_TARGET_TEXT'
    | 'GENERATING_TARGET_AUDIO'
    | 'COMPLETED'
    | 'FAILED';