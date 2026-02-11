from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import json
import aiofiles
from datetime import datetime
from typing import Optional, List
import logging

from .services.audio_preprocessing_service import AudioPreprocessingService
from .services.transcription_service import TranscriptionService
from .services.text_formatting_service import TextFormattingService
from .services.translation_service import TranslationService
from .services.chunk_merging_service import ChunkMergingService
from .services.text_cleaning_service import TextCleaningService
from .services.tts_service import TTSService
from .models.translation_job import TranslationJob, JobStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audio Translation Service", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (backed by JSON files for persistence)
jobs_storage = {}

# Directory for job outputs
OUTPUTS_DIR = "/app/outputs"

def get_job_json_path(job_id: str) -> str:
    """Get the path to the job's JSON file"""
    return os.path.join(OUTPUTS_DIR, job_id, "job.json")

def save_job_to_disk(job: TranslationJob) -> None:
    """Save job data to JSON file for persistence"""
    try:
        job_dir = os.path.join(OUTPUTS_DIR, job.job_id)
        os.makedirs(job_dir, exist_ok=True)

        job_path = get_job_json_path(job.job_id)
        job_data = job.model_dump()

        # Convert enum to string value
        if job_data.get('status'):
            status = job_data['status']
            job_data['status'] = status.value if hasattr(status, 'value') else str(status)

        # Convert datetime objects to ISO format strings
        if job_data.get('created_at'):
            job_data['created_at'] = job_data['created_at'].isoformat()
        if job_data.get('completed_at'):
            job_data['completed_at'] = job_data['completed_at'].isoformat()

        with open(job_path, 'w') as f:
            json.dump(job_data, f, indent=2)

        logger.info(f"Saved job {job.job_id} to disk")
    except Exception as e:
        logger.error(f"Failed to save job {job.job_id} to disk: {e}")

def load_job_from_disk(job_id: str) -> Optional[TranslationJob]:
    """Load job data from JSON file"""
    try:
        job_path = get_job_json_path(job_id)
        if not os.path.exists(job_path):
            return None

        with open(job_path, 'r') as f:
            job_data = json.load(f)

        # Convert ISO format strings back to datetime objects
        if job_data.get('created_at'):
            job_data['created_at'] = datetime.fromisoformat(job_data['created_at'])
        if job_data.get('completed_at'):
            job_data['completed_at'] = datetime.fromisoformat(job_data['completed_at'])

        # Convert status string back to enum
        if job_data.get('status'):
            job_data['status'] = JobStatus(job_data['status'])

        return TranslationJob(**job_data)
    except Exception as e:
        logger.error(f"Failed to load job {job_id} from disk: {e}")
        return None

def load_all_jobs_from_disk() -> None:
    """Load all jobs from disk on startup"""
    try:
        if not os.path.exists(OUTPUTS_DIR):
            logger.info("No outputs directory found, starting fresh")
            return

        loaded_count = 0
        for job_id in os.listdir(OUTPUTS_DIR):
            job_dir = os.path.join(OUTPUTS_DIR, job_id)
            if os.path.isdir(job_dir):
                job = load_job_from_disk(job_id)
                if job:
                    jobs_storage[job_id] = job
                    loaded_count += 1

        logger.info(f"Loaded {loaded_count} jobs from disk")
    except Exception as e:
        logger.error(f"Failed to load jobs from disk: {e}")

# Load existing jobs on module import
load_all_jobs_from_disk()

def get_status_value(status) -> str:
    """Safely get status value whether it's an enum or string"""
    return status.value if hasattr(status, 'value') else str(status)

class TranslationRequest(BaseModel):
    job_id: str
    user_id: int
    original_filename: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    error: Optional[str] = None
    files: List[dict] = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "audio-translation"}

@app.post("/translation/upload")
async def upload_audio_file(
    background_tasks: BackgroundTasks,
    user_id: int,
    file: UploadFile = File(...),
    source_language: str = "en",
    target_language: str = "ja"
):
    """Upload audio file and start translation job"""

    # Validate language parameters
    valid_languages = ["en", "ja"]
    if source_language not in valid_languages:
        raise HTTPException(status_code=400, detail=f"Invalid source_language. Supported: {valid_languages}")
    if target_language not in valid_languages:
        raise HTTPException(status_code=400, detail=f"Invalid target_language. Supported: {valid_languages}")
    if source_language == target_language:
        raise HTTPException(status_code=400, detail="source_language and target_language must be different")

    # Validate file type
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: mp3, wav, m4a, flac")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create uploads directory
    upload_dir = "/app/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save uploaded file
    file_path = os.path.join(upload_dir, f"{job_id}_{file.filename}")

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Create translation job
    job = TranslationJob(
        job_id=job_id,
        user_id=user_id,
        original_filename=file.filename,
        original_file_path=file_path,
        status=JobStatus.UPLOADED,
        created_at=datetime.now(),
        source_language=source_language,
        target_language=target_language
    )

    jobs_storage[job_id] = job
    save_job_to_disk(job)  # Persist to JSON file

    logger.info(f"Created job {job_id} with translation direction: {source_language} -> {target_language}")

    # Start processing in background
    background_tasks.add_task(process_translation_job, job_id)

    return {
        "job_id": job_id,
        "status": "uploaded",
        "message": f"File uploaded successfully. Processing started ({source_language.upper()} → {target_language.upper()})."
    }

@app.get("/translation/status/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get translation job status"""

    # Try in-memory first, then fall back to disk
    if job_id not in jobs_storage:
        # Try to load from disk
        job = load_job_from_disk(job_id)
        if job:
            jobs_storage[job_id] = job  # Cache in memory
            logger.info(f"Loaded job {job_id} from disk into memory")
        else:
            raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]
    
    files = []
    if job.formatted_transcript_path and os.path.exists(job.formatted_transcript_path):
        files.append({"type": "source_transcript", "available": True})
    if job.clean_target_path and os.path.exists(job.clean_target_path):
        files.append({"type": "target_transcript", "available": True})
    if job.final_target_audio_path and os.path.exists(job.final_target_audio_path):
        files.append({"type": "target_audio", "available": True})
    
    return JobStatusResponse(
        job_id=job_id,
        status=get_status_value(job.status),
        progress=job.progress,
        message=job.message,
        error=job.error_message,
        files=files
    )

@app.get("/translation/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Download translation result files"""

    # Try in-memory first, then fall back to disk
    if job_id not in jobs_storage:
        job = load_job_from_disk(job_id)
        if job:
            jobs_storage[job_id] = job
            logger.info(f"Loaded job {job_id} from disk for download")
        else:
            raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]

    file_path = None
    media_type = "text/plain"

    # Support both old (english_transcript, japanese_transcript, japanese_audio)
    # and new (source_transcript, target_transcript, target_audio) file types for backwards compatibility
    if file_type in ["english_transcript", "source_transcript"]:
        file_path = job.formatted_transcript_path
        media_type = "text/plain"
    elif file_type in ["japanese_transcript", "target_transcript"]:
        file_path = job.clean_target_path
        media_type = "text/plain"
    elif file_type in ["japanese_audio", "target_audio"]:
        file_path = job.final_target_audio_path
        media_type = "audio/mpeg"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    filename = os.path.basename(file_path)
    return FileResponse(file_path, media_type=media_type, filename=filename)

@app.get("/translation/jobs/{user_id}")
async def get_user_jobs(user_id: int):
    """Get all translation jobs for a user"""

    user_jobs = [
        {
            "job_id": job.job_id,
            "original_filename": job.original_filename,
            "status": get_status_value(job.status),
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        for job in jobs_storage.values()
        if job.user_id == user_id
    ]

    return {"jobs": user_jobs}

# Test endpoint for retry logic - only available when TEST_MODE=true
@app.post("/translation/test/fail/{job_id}")
async def simulate_job_failure(job_id: str, failure_step: str):
    """TEST ONLY: Simulate a job failure at a specific step for retry testing"""
    
    # Check if test mode is enabled
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    if not test_mode:
        raise HTTPException(status_code=404, detail="Test endpoints not available (TEST_MODE=false)")
    
    # Try in-memory first, then fall back to disk
    if job_id not in jobs_storage:
        job = load_job_from_disk(job_id)
        if job:
            jobs_storage[job_id] = job
            logger.info(f"Loaded job {job_id} from disk for test")
        else:
            raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]

    # Map failure steps to status enums
    failure_mapping = {
        "preprocessing": JobStatus.FAILED_PREPROCESSING_AUDIO,
        "transcription": JobStatus.FAILED_TRANSCRIBING_SOURCE,
        "formatting": JobStatus.FAILED_FORMATTING_SOURCE_TEXT,
        "translation": JobStatus.FAILED_TRANSLATING_TO_TARGET,
        "merging": JobStatus.FAILED_MERGING_TARGET_CHUNKS,
        "cleaning": JobStatus.FAILED_CLEANING_TARGET_TEXT,
        "audio_generation": JobStatus.FAILED_GENERATING_TARGET_AUDIO,
        "generic": JobStatus.FAILED
    }
    
    if failure_step not in failure_mapping:
        available_steps = ", ".join(failure_mapping.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid failure step. Available: {available_steps}"
        )
    
    # Set the job to failed status at that specific step
    job.status = failure_mapping[failure_step]
    job.error_message = f"TEST: Simulated failure at {failure_step} step"
    job.message = f"Test failure at {failure_step} step - ready for retry testing"
    
    # Set realistic progress based on failure point (simulates partial completion)
    progress_mapping = {
        "preprocessing": 10,
        "transcription": 30,
        "formatting": 50,
        "translation": 65,
        "merging": 78,
        "cleaning": 83,
        "audio_generation": 95,
        "generic": 50
    }
    job.progress = progress_mapping[failure_step]
    save_job_to_disk(job)  # Persist test failure state

    logger.info(f"TEST: Simulated {failure_step} failure for job {job_id} (TEST_MODE enabled)")
    
    return {
        "job_id": job_id,
        "status": get_status_value(job.status),
        "message": f"✅ Test failure injected at '{failure_step}' step. Progress set to {job.progress}%. You can now test the retry functionality!",
        "progress": job.progress,
        "test_mode": True
    }

@app.post("/translation/retry/{job_id}")
async def retry_job(job_id: str, background_tasks: BackgroundTasks):
    """Retry a failed translation job from the last successful step"""

    # Try in-memory first, then fall back to disk
    if job_id not in jobs_storage:
        job = load_job_from_disk(job_id)
        if job:
            jobs_storage[job_id] = job
            logger.info(f"Loaded job {job_id} from disk for retry")
        else:
            raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]
    
    # Only allow retry for failed jobs (any failure status)
    failed_status_values = [
        "FAILED",
        "FAILED_PREPROCESSING_AUDIO",
        "FAILED_TRANSCRIBING_SOURCE",
        "FAILED_FORMATTING_SOURCE_TEXT",
        "FAILED_TRANSLATING_TO_TARGET",
        "FAILED_MERGING_TARGET_CHUNKS",
        "FAILED_CLEANING_TARGET_TEXT",
        "FAILED_GENERATING_TARGET_AUDIO"
    ]

    current_status = get_status_value(job.status)
    if current_status not in failed_status_values:
        raise HTTPException(status_code=400, detail=f"Cannot retry job with status: {current_status}")
    
    # Reset error state
    job.error_message = None
    job.message = "Retrying job from last successful step..."
    save_job_to_disk(job)  # Persist retry state

    # Start retry processing in background
    background_tasks.add_task(process_translation_job, job_id, is_retry=True)
    
    return {
        "job_id": job_id,
        "status": "retrying",
        "message": "Job retry started from last successful step."
    }

def determine_resume_point(job: TranslationJob):
    """Determine which step to resume from based on failure status or existing files"""

    # If we have a specific failure status, resume from that exact step
    # Use string values for comparison to handle both enum and string status
    failure_to_resume_map = {
        "FAILED_PREPROCESSING_AUDIO": JobStatus.PREPROCESSING_AUDIO,
        "FAILED_TRANSCRIBING_SOURCE": JobStatus.TRANSCRIBING_SOURCE,
        "FAILED_FORMATTING_SOURCE_TEXT": JobStatus.FORMATTING_SOURCE_TEXT,
        "FAILED_TRANSLATING_TO_TARGET": JobStatus.TRANSLATING_TO_TARGET,
        "FAILED_MERGING_TARGET_CHUNKS": JobStatus.MERGING_TARGET_CHUNKS,
        "FAILED_CLEANING_TARGET_TEXT": JobStatus.CLEANING_TARGET_TEXT,
        "FAILED_GENERATING_TARGET_AUDIO": JobStatus.GENERATING_TARGET_AUDIO,
    }

    current_status = get_status_value(job.status)
    if current_status in failure_to_resume_map:
        return failure_to_resume_map[current_status]

    # For generic FAILED status or other cases, use file-based detection
    # Check files in reverse order of creation
    if job.final_target_audio_path and os.path.exists(job.final_target_audio_path):
        return JobStatus.COMPLETED  # Job is actually complete

    if job.clean_target_path and os.path.exists(job.clean_target_path):
        return JobStatus.GENERATING_TARGET_AUDIO

    if job.merged_target_path and os.path.exists(job.merged_target_path):
        return JobStatus.CLEANING_TARGET_TEXT

    if job.translation_chunks_dir and os.path.exists(job.translation_chunks_dir):
        return JobStatus.MERGING_TARGET_CHUNKS

    if job.formatted_transcript_path and os.path.exists(job.formatted_transcript_path):
        return JobStatus.TRANSLATING_TO_TARGET

    if job.raw_transcript_path and os.path.exists(job.raw_transcript_path):
        return JobStatus.FORMATTING_SOURCE_TEXT

    if job.chunks_dir and os.path.exists(job.chunks_dir):
        return JobStatus.TRANSCRIBING_SOURCE

    if job.processed_audio_dir and os.path.exists(job.processed_audio_dir):
        return JobStatus.PREPROCESSING_AUDIO

    # Start from the beginning
    return JobStatus.UPLOADED

async def process_translation_job(job_id: str, is_retry: bool = False):
    """Background task to process translation job following the 3-step workflow"""
    
    job = jobs_storage[job_id]
    
    try:
        # Determine starting point for retry or fresh start
        if is_retry:
            resume_from = determine_resume_point(job)
            logger.info(f"Retrying translation job {job_id} from step {resume_from.value}")
            job.message = f"Retrying from step: {resume_from.value}"
        else:
            resume_from = JobStatus.UPLOADED
            logger.info(f"Starting translation job {job_id}")
        
        # Initialize service instances
        preprocessing_service = AudioPreprocessingService()
        transcription_service = TranscriptionService()
        formatting_service = TextFormattingService()
        translation_service = TranslationService()
        merging_service = ChunkMergingService()
        cleaning_service = TextCleaningService()
        tts_service = TTSService()
        
        # === STEP 1: EXTRACT SOURCE TEXT ===

        # Step 1.1: Preprocess Audio
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO]:
            try:
                job.status = JobStatus.PREPROCESSING_AUDIO
                job.progress = 5
                job.message = "Preprocessing audio - cleaning and creating chunks..."

                processed_dir = f"/app/outputs/{job_id}/processed"

                cleaned_audio_path, chunks_dir = await preprocessing_service.preprocess_audio(
                    job.original_file_path, processed_dir
                )

                job.processed_audio_dir = processed_dir
                job.chunks_dir = chunks_dir
                job.progress = 15
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Audio preprocessing completed")
            except Exception as e:
                logger.error(f"Job {job_id}: Audio preprocessing failed: {e}")
                job.status = JobStatus.FAILED_PREPROCESSING_AUDIO
                job.error_message = str(e)
                job.message = f"Audio preprocessing failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # Step 1.2: Transcribe with AssemblyAI
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO, JobStatus.TRANSCRIBING_SOURCE]:
            try:
                job.status = JobStatus.TRANSCRIBING_SOURCE
                job.progress = 20
                source_lang_name = "English" if job.source_language == "en" else "Japanese"
                job.message = f"Transcribing {source_lang_name} audio with speaker diarization..."

                raw_transcript_path = f"/app/outputs/{job_id}/transcript_{job.source_language}_raw.txt"

                await transcription_service.transcribe_chunks(job.chunks_dir, raw_transcript_path, job.source_language)
                job.raw_transcript_path = raw_transcript_path
                job.progress = 40
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Transcription completed ({job.source_language})")
            except Exception as e:
                logger.error(f"Job {job_id}: Transcription failed: {e}")
                job.status = JobStatus.FAILED_TRANSCRIBING_SOURCE
                job.error_message = str(e)
                job.message = f"Transcription failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # Step 1.3: Format Text
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO, JobStatus.TRANSCRIBING_SOURCE, JobStatus.FORMATTING_SOURCE_TEXT]:
            try:
                job.status = JobStatus.FORMATTING_SOURCE_TEXT
                job.progress = 45
                source_lang_name = "English" if job.source_language == "en" else "Japanese"
                job.message = f"Formatting {source_lang_name} transcript with speaker tags..."

                formatted_transcript_path = f"/app/outputs/{job_id}/transcript_{job.source_language}_formatted.txt"

                await formatting_service.format_transcript(job.raw_transcript_path, formatted_transcript_path)
                job.formatted_transcript_path = formatted_transcript_path
                job.progress = 50
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Text formatting completed")
            except Exception as e:
                logger.error(f"Job {job_id}: Text formatting failed: {e}")
                job.status = JobStatus.FAILED_FORMATTING_SOURCE_TEXT
                job.error_message = str(e)
                job.message = f"Text formatting failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # === STEP 2: TRANSLATE TO TARGET LANGUAGE ===

        # Step 2.1: Translate in Chunks
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO, JobStatus.TRANSCRIBING_SOURCE, JobStatus.FORMATTING_SOURCE_TEXT, JobStatus.TRANSLATING_TO_TARGET]:
            try:
                job.status = JobStatus.TRANSLATING_TO_TARGET
                job.progress = 55
                source_lang_name = "English" if job.source_language == "en" else "Japanese"
                target_lang_name = "Japanese" if job.target_language == "ja" else "English"
                job.message = f"Translating {source_lang_name} to {target_lang_name} in chunks..."

                translation_chunks_dir = f"/app/outputs/{job_id}/translation_chunks"

                await translation_service.translate_text(
                    job.formatted_transcript_path,
                    translation_chunks_dir,
                    job.source_language,
                    job.target_language
                )
                job.translation_chunks_dir = translation_chunks_dir
                job.progress = 70
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Translation completed ({job.source_language} -> {job.target_language})")
            except Exception as e:
                logger.error(f"Job {job_id}: Translation failed: {e}")
                job.status = JobStatus.FAILED_TRANSLATING_TO_TARGET
                job.error_message = str(e)
                job.message = f"Translation failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # Step 2.2: Merge Chunks
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO, JobStatus.TRANSCRIBING_SOURCE, JobStatus.FORMATTING_SOURCE_TEXT, JobStatus.TRANSLATING_TO_TARGET, JobStatus.MERGING_TARGET_CHUNKS]:
            try:
                job.status = JobStatus.MERGING_TARGET_CHUNKS
                job.progress = 75
                target_lang_name = "Japanese" if job.target_language == "ja" else "English"
                job.message = f"Merging {target_lang_name} translation chunks..."

                merged_path = f"/app/outputs/{job_id}/transcript_{job.target_language}_merged.txt"

                await merging_service.merge_translation_chunks(job.translation_chunks_dir, merged_path)
                job.merged_target_path = merged_path
                job.progress = 80
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Chunk merging completed")
            except Exception as e:
                logger.error(f"Job {job_id}: Chunk merging failed: {e}")
                job.status = JobStatus.FAILED_MERGING_TARGET_CHUNKS
                job.error_message = str(e)
                job.message = f"Chunk merging failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # Step 2.3: Clean Target Text
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO, JobStatus.TRANSCRIBING_SOURCE, JobStatus.FORMATTING_SOURCE_TEXT, JobStatus.TRANSLATING_TO_TARGET, JobStatus.MERGING_TARGET_CHUNKS, JobStatus.CLEANING_TARGET_TEXT]:
            try:
                job.status = JobStatus.CLEANING_TARGET_TEXT
                job.progress = 82
                target_lang_name = "Japanese" if job.target_language == "ja" else "English"
                job.message = f"Cleaning {target_lang_name} text - removing artifacts..."

                clean_path = f"/app/outputs/{job_id}/transcript_{job.target_language}_clean.txt"

                await cleaning_service.clean_text(job.merged_target_path, clean_path, job.target_language)
                job.clean_target_path = clean_path
                job.progress = 85
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Text cleaning completed")
            except Exception as e:
                logger.error(f"Job {job_id}: Text cleaning failed: {e}")
                job.status = JobStatus.FAILED_CLEANING_TARGET_TEXT
                job.error_message = str(e)
                job.message = f"Text cleaning failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # === STEP 3: GENERATE TARGET AUDIO ===

        # Step 3.1: Generate Audio with Google TTS
        if resume_from in [JobStatus.UPLOADED, JobStatus.PREPROCESSING_AUDIO, JobStatus.TRANSCRIBING_SOURCE, JobStatus.FORMATTING_SOURCE_TEXT, JobStatus.TRANSLATING_TO_TARGET, JobStatus.MERGING_TARGET_CHUNKS, JobStatus.CLEANING_TARGET_TEXT, JobStatus.GENERATING_TARGET_AUDIO]:
            try:
                job.status = JobStatus.GENERATING_TARGET_AUDIO
                job.progress = 90
                target_lang_name = "Japanese" if job.target_language == "ja" else "English"
                job.message = f"Generating {target_lang_name} audio with speaker voices..."

                audio_output_dir = f"/app/outputs/{job_id}/audio_segments"
                final_audio_path = f"/app/outputs/{job_id}/full_audio_{job.target_language}.mp3"

                await tts_service.generate_audio(
                    job.clean_target_path,
                    audio_output_dir,
                    final_audio_path,
                    job.target_language
                )

                job.audio_output_dir = audio_output_dir
                job.final_target_audio_path = final_audio_path
                job.progress = 100
                save_job_to_disk(job)
                logger.info(f"Job {job_id}: Audio generation completed ({job.target_language})")
            except Exception as e:
                logger.error(f"Job {job_id}: Audio generation failed: {e}")
                job.status = JobStatus.FAILED_GENERATING_TARGET_AUDIO
                job.error_message = str(e)
                job.message = f"Audio generation failed: {str(e)}"
                save_job_to_disk(job)
                return
        
        # Mark as completed
        job.status = JobStatus.COMPLETED
        job.message = "Translation completed successfully! 🎉"
        job.completed_at = datetime.now()
        save_job_to_disk(job)

        if is_retry:
            logger.info(f"Translation job {job_id} retry completed successfully")
        else:
            logger.info(f"Translation job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Translation job {job_id} failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.message = f"Translation failed: {str(e)}"
        save_job_to_disk(job)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)