from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
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

# In-memory job storage (in production, use Redis or database)
jobs_storage = {}

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
    file: UploadFile = File(...)
):
    """Upload audio file and start translation job"""
    
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
        status=JobStatus.UPLOADED_EN,
        created_at=datetime.now()
    )
    
    jobs_storage[job_id] = job
    
    # Start processing in background
    background_tasks.add_task(process_translation_job, job_id)
    
    return {
        "job_id": job_id,
        "status": "uploaded",
        "message": "File uploaded successfully. Processing started."
    }

@app.get("/translation/status/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get translation job status"""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    files = []
    if job.formatted_transcript_path and os.path.exists(job.formatted_transcript_path):
        files.append({"type": "english_transcript", "available": True})
    if job.clean_japanese_path and os.path.exists(job.clean_japanese_path):
        files.append({"type": "japanese_transcript", "available": True})
    if job.final_japanese_audio_path and os.path.exists(job.final_japanese_audio_path):
        files.append({"type": "japanese_audio", "available": True})
    
    return JobStatusResponse(
        job_id=job_id,
        status=job.status.value,
        progress=job.progress,
        message=job.message,
        error=job.error_message,
        files=files
    )

@app.get("/translation/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Download translation result files"""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    file_path = None
    media_type = "text/plain"
    
    if file_type == "english_transcript":
        file_path = job.formatted_transcript_path
        media_type = "text/plain"
    elif file_type == "japanese_transcript":
        file_path = job.clean_japanese_path
        media_type = "text/plain"
    elif file_type == "japanese_audio":
        file_path = job.final_japanese_audio_path
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
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        for job in jobs_storage.values()
        if job.user_id == user_id
    ]
    
    return {"jobs": user_jobs}

async def process_translation_job(job_id: str):
    """Background task to process translation job following the 3-step workflow"""
    
    job = jobs_storage[job_id]
    
    try:
        logger.info(f"Starting translation job {job_id}")
        
        # === STEP 1: EXTRACT ENGLISH TEXT ===
        
        # Step 1.1: Preprocess Audio
        job.status = JobStatus.PREPROCESSING_AUDIO_EN
        job.progress = 5
        job.message = "Preprocessing audio - cleaning and creating chunks..."
        
        preprocessing_service = AudioPreprocessingService()
        processed_dir = f"/app/outputs/{job_id}/processed"
        
        cleaned_audio_path, chunks_dir = await preprocessing_service.preprocess_audio(
            job.original_file_path, processed_dir
        )
        
        job.processed_audio_dir = processed_dir
        job.chunks_dir = chunks_dir
        job.progress = 15
        
        # Step 1.2: Transcribe with AssemblyAI
        job.status = JobStatus.TRANSCRIBING_EN
        job.progress = 20
        job.message = "Transcribing English audio with speaker diarization..."
        
        transcription_service = TranscriptionService()
        raw_transcript_path = f"/app/outputs/{job_id}/transcript_en_raw.txt"
        
        await transcription_service.transcribe_chunks(chunks_dir, raw_transcript_path)
        job.raw_transcript_path = raw_transcript_path
        job.progress = 40
        
        # Step 1.3: Format Text
        job.status = JobStatus.FORMATTING_TEXT_EN
        job.progress = 45
        job.message = "Formatting English transcript with speaker tags..."
        
        formatting_service = TextFormattingService()
        formatted_transcript_path = f"/app/outputs/{job_id}/transcript_en_formatted.txt"
        
        await formatting_service.format_transcript(raw_transcript_path, formatted_transcript_path)
        job.formatted_transcript_path = formatted_transcript_path
        job.progress = 50
        
        # === STEP 2: TRANSLATE TO JAPANESE ===
        
        # Step 2.1: Translate in Chunks
        job.status = JobStatus.TRANSLATING_CHUNKS_JP
        job.progress = 55
        job.message = "Translating English to Japanese in chunks..."
        
        translation_service = TranslationService()
        translation_chunks_dir = f"/app/outputs/{job_id}/translation_chunks"
        
        await translation_service.translate_to_japanese(formatted_transcript_path, translation_chunks_dir)
        job.translation_chunks_dir = translation_chunks_dir
        job.progress = 70
        
        # Step 2.2: Merge Chunks
        job.status = JobStatus.MERGING_CHUNKS_JP
        job.progress = 75
        job.message = "Merging Japanese translation chunks..."
        
        merging_service = ChunkMergingService()
        merged_japanese_path = f"/app/outputs/{job_id}/transcript_ja_merged.txt"
        
        await merging_service.merge_translation_chunks(translation_chunks_dir, merged_japanese_path)
        job.merged_japanese_path = merged_japanese_path
        job.progress = 80
        
        # Step 2.3: Clean Japanese Text
        job.status = JobStatus.CLEANING_TEXT_JP
        job.progress = 82
        job.message = "Cleaning Japanese text - removing artifacts..."
        
        cleaning_service = TextCleaningService()
        clean_japanese_path = f"/app/outputs/{job_id}/transcript_ja_clean.txt"
        
        await cleaning_service.clean_japanese_text(merged_japanese_path, clean_japanese_path)
        job.clean_japanese_path = clean_japanese_path
        job.progress = 85
        
        # === STEP 3: GENERATE JAPANESE AUDIO ===
        
        # Step 3.1: Generate Audio with Google TTS
        job.status = JobStatus.GENERATING_AUDIO_JP
        job.progress = 90
        job.message = "Generating Japanese audio with speaker voices..."
        
        tts_service = TTSService()
        audio_output_dir = f"/app/outputs/{job_id}/audio_segments"
        final_audio_path = f"/app/outputs/{job_id}/full_audio_jp.mp3"
        
        await tts_service.generate_japanese_audio(
            clean_japanese_path, 
            audio_output_dir, 
            final_audio_path
        )
        
        job.audio_output_dir = audio_output_dir
        job.final_japanese_audio_path = final_audio_path
        job.progress = 100
        job.status = JobStatus.COMPLETED
        job.message = "Translation completed successfully! 🎉"
        job.completed_at = datetime.now()
        
        logger.info(f"Translation job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Translation job {job_id} failed: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.message = f"Translation failed: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)