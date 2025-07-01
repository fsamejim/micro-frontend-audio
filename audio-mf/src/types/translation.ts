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
    type: 'english_transcript' | 'japanese_transcript' | 'japanese_audio';
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
    | 'uploaded' 
    | 'preprocessing_audio_en' 
    | 'transcribing_en'
    | 'formatting_text_en'
    | 'translating_chunks_jp'
    | 'merging_chunks_jp'
    | 'cleaning_text_jp'
    | 'generating_audio_jp'
    | 'completed'
    | 'failed';