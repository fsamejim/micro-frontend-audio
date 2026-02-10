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
}

export interface TranslationFile {
    type: 'source_transcript' | 'target_transcript' | 'target_audio';
    available: boolean;
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
}

export interface UserJobsResponse {
    jobs: TranslationJob[];
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