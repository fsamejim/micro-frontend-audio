import os
import asyncio
from pathlib import Path
from pydub import AudioSegment, effects, silence
from pydub.utils import which
import logging

logger = logging.getLogger(__name__)

class AudioPreprocessingService:
    """
    Audio Preprocessing Script
    - Normalize audio to improve transcription accuracy
    - Remove silence and clean the audio
    - Perform smart silence-aware chunking (4-6 min)
    """
    
    def __init__(self):
        # Ensure ffmpeg is available
        AudioSegment.converter = which("ffmpeg")
        AudioSegment.ffmpeg = which("ffmpeg")
        AudioSegment.ffprobe = which("ffprobe")
        
        # Audio preprocessing settings from your base code
        self.target_sample_rate = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))
        self.padding_ms = int(os.getenv("PADDING_MS", "500"))
        self.normalization_target_dbfs = int(os.getenv("NORMALIZATION_TARGET_DBFS", "-20"))
        self.min_chunk_ms = int(os.getenv("MIN_CHUNK_MS", str(4 * 60 * 1000)))  # 4 minutes
        self.max_chunk_ms = int(os.getenv("MAX_CHUNK_MS", str(6 * 60 * 1000)))  # 6 minutes
    
    async def preprocess_audio(self, input_audio_path: str, output_dir: str) -> tuple[str, str]:
        """
        Preprocess audio file - clean and create chunks
        
        Args:
            input_audio_path: Path to original audio file
            output_dir: Directory to save processed audio and chunks
            
        Returns:
            tuple: (processed_audio_path, chunks_dir_path)
        """
        
        try:
            # Create output directories
            processed_audio_dir = os.path.join(output_dir, "processed_audio")
            chunks_dir = os.path.join(processed_audio_dir, "chunks")
            os.makedirs(chunks_dir, exist_ok=True)
            
            logger.info(f"Starting audio preprocessing: {input_audio_path}")
            
            # Load and preprocess audio (matching your base code)
            audio = AudioSegment.from_file(input_audio_path).set_channels(1).set_frame_rate(self.target_sample_rate)
            
            # Normalize loudness to improve transcription accuracy
            normalized_audio = effects.normalize(audio)
            if normalized_audio.dBFS < self.normalization_target_dbfs:
                gain_needed = self.normalization_target_dbfs - normalized_audio.dBFS
                logger.info(f"Boosting volume by {gain_needed:.2f} dB")
                normalized_audio = normalized_audio.apply_gain(gain_needed)
            
            logger.info(f"Volume after normalization: {normalized_audio.dBFS:.2f} dBFS")
            
            # Silence threshold: adapt based on actual audio loudness
            silence_thresh_db = min(-40, normalized_audio.dBFS - 10)
            logger.info(f"Silence threshold set to: {silence_thresh_db:.2f} dBFS")
            
            # Detect non-silent regions and clean audio
            nonsilent_ranges = silence.detect_nonsilent(
                normalized_audio,
                min_silence_len=500,
                silence_thresh=silence_thresh_db
            )
            
            # Remove silence (matching your base code logic)
            if not nonsilent_ranges:
                logger.warning("No silent segments detected — processing full audio without trimming")
                cleaned_audio = normalized_audio
            else:
                cleaned_audio = AudioSegment.silent(duration=0)
                for start_ms, end_ms in nonsilent_ranges:
                    start_ms = max(0, start_ms - self.padding_ms)
                    end_ms = min(len(normalized_audio), end_ms + self.padding_ms)
                    cleaned_audio += normalized_audio[start_ms:end_ms]
            
            # Report final cleaned length
            cleaned_duration_sec = len(cleaned_audio) / 1000
            logger.info(f"Cleaned duration: {cleaned_duration_sec:.2f} seconds")
            
            # Save cleaned WAV file
            base_name = Path(input_audio_path).stem
            cleaned_audio_path = os.path.join(processed_audio_dir, f"{base_name}_cleaned.wav")
            cleaned_audio.export(cleaned_audio_path, format="wav")
            logger.info(f"Cleaned audio saved: {cleaned_audio_path}")
            
            # Smart chunking: short audio gets single chunk, long audio gets smart chunking
            if len(cleaned_audio) <= self.max_chunk_ms:
                logger.info("Audio is short — saving as single chunk")
                chunk_path = os.path.join(chunks_dir, "chunk_001.wav")
                cleaned_audio.export(chunk_path, format="wav")
                logger.info(f"Created single chunk: chunk_001.wav")
            else:
                logger.info("Audio is long — performing smart silence-aware chunking")
                await self._smart_chunk_audio(cleaned_audio, chunks_dir)
            
            logger.info(f"Audio preprocessing completed. Chunks saved in: {chunks_dir}")
            
            return cleaned_audio_path, chunks_dir
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise Exception(f"Audio preprocessing failed: {str(e)}")
    
    async def get_audio_info(self, audio_path: str) -> dict:
        """Get audio file information"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return {
                "duration_seconds": len(audio) / 1000,
                "channels": audio.channels,
                "frame_rate": audio.frame_rate,
                "sample_width": audio.sample_width,
                "format": audio_path.split('.')[-1].lower()
            }
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {}
    
    async def _smart_chunk_audio(self, audio: AudioSegment, output_dir: str):
        """
        Split audio intelligently on silence, aiming for chunks between min and max duration
        Matches your base code smart_chunk_audio() function
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Detect silence ranges to find split points
        silence_thresh_db = min(-40, audio.dBFS - 10)
        silent_ranges = silence.detect_silence(
            audio,
            min_silence_len=300,
            silence_thresh=silence_thresh_db
        )
        
        logger.info(f"Found {len(silent_ranges)} silence ranges for smart chunking")
        
        current_pos = 0
        chunk_index = 1
        
        while current_pos < len(audio):
            target_end = min(current_pos + self.max_chunk_ms, len(audio))
            
            # Find nearest silence point after min_chunk_ms
            candidate_silences = [
                s for s in silent_ranges if current_pos + self.min_chunk_ms <= s[0] <= target_end
            ]
            
            best_split = candidate_silences[0][0] if candidate_silences else target_end
            
            # Extract chunk and export
            chunk = audio[current_pos:best_split]
            chunk_filename = os.path.join(output_dir, f"chunk_{chunk_index:03d}.wav")
            chunk.export(chunk_filename, format="wav")
            logger.info(f"Created smart chunk: chunk_{chunk_index:03d}.wav ({len(chunk)/1000:.2f} sec)")
            
            current_pos = best_split
            chunk_index += 1
        
        logger.info("Smart chunking completed")