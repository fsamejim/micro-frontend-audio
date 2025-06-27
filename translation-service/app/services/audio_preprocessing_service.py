import os
import asyncio
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import which
import logging

logger = logging.getLogger(__name__)

class AudioPreprocessingService:
    """
    Mirrors the functionality of preprocess_audio.py
    Converts audio to better quality/format and creates chunks
    """
    
    def __init__(self):
        # Ensure ffmpeg is available
        AudioSegment.converter = which("ffmpeg")
        AudioSegment.ffmpeg = which("ffmpeg")
        AudioSegment.ffprobe = which("ffprobe")
    
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
            
            # Load audio file
            audio = AudioSegment.from_file(input_audio_path)
            
            # Clean audio - normalize volume, remove silence
            # Normalize to -20dBFS (good level for speech)
            normalized_audio = audio.normalize().apply_gain(-20 - audio.dBFS)
            
            # Convert to WAV format for better quality
            base_name = Path(input_audio_path).stem
            cleaned_audio_path = os.path.join(processed_audio_dir, f"{base_name}_cleaned.wav")
            
            # Export cleaned full audio
            normalized_audio.export(
                cleaned_audio_path, 
                format="wav",
                parameters=["-ac", "1", "-ar", "16000"]  # Mono, 16kHz for speech recognition
            )
            
            logger.info(f"Cleaned audio saved: {cleaned_audio_path}")
            
            # Create chunks (5-minute segments for API processing)
            chunk_length_ms = 5 * 60 * 1000  # 5 minutes
            total_chunks = len(normalized_audio) // chunk_length_ms + 1
            
            logger.info(f"Creating {total_chunks} audio chunks...")
            
            for i in range(total_chunks):
                start_ms = i * chunk_length_ms
                end_ms = min((i + 1) * chunk_length_ms, len(normalized_audio))
                
                if start_ms >= len(normalized_audio):
                    break
                    
                chunk = normalized_audio[start_ms:end_ms]
                chunk_filename = f"chunk_{i+1:03d}.wav"
                chunk_path = os.path.join(chunks_dir, chunk_filename)
                
                chunk.export(
                    chunk_path,
                    format="wav",
                    parameters=["-ac", "1", "-ar", "16000"]
                )
                
                logger.info(f"Created chunk: {chunk_filename}")
            
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