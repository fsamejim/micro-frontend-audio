from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class JobStatus(Enum):
    UPLOADED_EN = "UPLOADED_EN"
    PREPROCESSING_AUDIO_EN = "PREPROCESSING_AUDIO_EN"
    TRANSCRIBING_EN = "TRANSCRIBING_EN"
    FORMATTING_TEXT_EN = "FORMATTING_TEXT_EN"
    TRANSLATING_CHUNKS_JP = "TRANSLATING_CHUNKS_JP"
    MERGING_CHUNKS_JP = "MERGING_CHUNKS_JP"
    CLEANING_TEXT_JP = "CLEANING_TEXT_JP"
    GENERATING_AUDIO_JP = "GENERATING_AUDIO_JP"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TranslationJob(BaseModel):
    job_id: str
    user_id: int
    original_filename: str
    status: JobStatus = JobStatus.UPLOADED_EN
    progress: int = 0
    message: str = ""
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # File paths for each step
    original_file_path: Optional[str] = None
    
    # Step 1: Extract English text paths
    processed_audio_dir: Optional[str] = None
    chunks_dir: Optional[str] = None
    raw_transcript_path: Optional[str] = None
    formatted_transcript_path: Optional[str] = None
    
    # Step 2: Japanese translation paths
    translation_chunks_dir: Optional[str] = None
    merged_japanese_path: Optional[str] = None
    clean_japanese_path: Optional[str] = None
    
    # Step 3: Japanese audio generation paths
    audio_output_dir: Optional[str] = None
    final_japanese_audio_path: Optional[str] = None
    
    # Resume tracking
    current_step: int = 1
    current_substep: int = 1
    
    class Config:
        use_enum_values = True