from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class JobStatus(Enum):
    UPLOADED = "UPLOADED"
    PREPROCESSING_AUDIO = "PREPROCESSING_AUDIO"
    TRANSCRIBING_SOURCE = "TRANSCRIBING_SOURCE"
    FORMATTING_SOURCE_TEXT = "FORMATTING_SOURCE_TEXT"
    TRANSLATING_TO_TARGET = "TRANSLATING_TO_TARGET"
    MERGING_TARGET_CHUNKS = "MERGING_TARGET_CHUNKS"
    CLEANING_TARGET_TEXT = "CLEANING_TARGET_TEXT"
    GENERATING_TARGET_AUDIO = "GENERATING_TARGET_AUDIO"
    COMPLETED = "COMPLETED"
    # Specific failure statuses for each step
    FAILED_PREPROCESSING_AUDIO = "FAILED_PREPROCESSING_AUDIO"
    FAILED_TRANSCRIBING_SOURCE = "FAILED_TRANSCRIBING_SOURCE"
    FAILED_FORMATTING_SOURCE_TEXT = "FAILED_FORMATTING_SOURCE_TEXT"
    FAILED_TRANSLATING_TO_TARGET = "FAILED_TRANSLATING_TO_TARGET"
    FAILED_MERGING_TARGET_CHUNKS = "FAILED_MERGING_TARGET_CHUNKS"
    FAILED_CLEANING_TARGET_TEXT = "FAILED_CLEANING_TARGET_TEXT"
    FAILED_GENERATING_TARGET_AUDIO = "FAILED_GENERATING_TARGET_AUDIO"
    FAILED = "FAILED"  # Generic fallback for unknown failures

class TranslationJob(BaseModel):
    job_id: str
    user_id: int
    original_filename: str
    status: JobStatus = JobStatus.UPLOADED
    progress: int = 0
    message: str = ""
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Language direction configuration
    source_language: str = "en"  # "en" or "ja"
    target_language: str = "ja"  # "ja" or "en"

    # File paths for each step
    original_file_path: Optional[str] = None

    # Step 1: Extract source text paths
    processed_audio_dir: Optional[str] = None
    chunks_dir: Optional[str] = None
    raw_transcript_path: Optional[str] = None
    formatted_transcript_path: Optional[str] = None

    # Step 2: Target translation paths
    translation_chunks_dir: Optional[str] = None
    merged_target_path: Optional[str] = None
    clean_target_path: Optional[str] = None

    # Step 3: Target audio generation paths
    audio_output_dir: Optional[str] = None
    final_target_audio_path: Optional[str] = None

    # Audio versions tracking for regeneration feature
    # Each version contains: {"version": 1, "path": "...", "voice_mappings": {...}, "speaking_rate": 1.2, "created_at": "..."}
    audio_versions: List[Dict[str, Any]] = []

    # Resume tracking
    current_step: int = 1
    current_substep: int = 1

    class Config:
        use_enum_values = True