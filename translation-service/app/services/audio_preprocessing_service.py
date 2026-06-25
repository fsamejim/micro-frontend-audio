import os
import asyncio
import subprocess
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AudioPreprocessingService:
    """
    Audio Preprocessing Service using ffmpeg directly for memory efficiency.
    - Streams audio processing to disk instead of loading into memory
    - Handles large files (200MB+) without memory spikes
    - Performs smart silence-aware chunking (4-6 min)
    """

    def __init__(self):
        self.target_sample_rate = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))
        self.min_chunk_ms = int(os.getenv("MIN_CHUNK_MS", str(240000)))  # 4 minutes
        self.max_chunk_ms = int(os.getenv("MAX_CHUNK_MS", str(360000)))  # 6 minutes
        self.min_chunk_sec = self.min_chunk_ms / 1000
        self.max_chunk_sec = self.max_chunk_ms / 1000

    async def preprocess_audio(self, input_audio_path: str, output_dir: str) -> tuple[str, str]:
        """
        Preprocess audio file - clean and create chunks using ffmpeg streaming.
        Memory-efficient: never loads full audio into memory.
        """
        return await asyncio.to_thread(
            self._preprocess_audio_sync,
            input_audio_path,
            output_dir
        )

    def _preprocess_audio_sync(self, input_audio_path: str, output_dir: str) -> tuple[str, str]:
        """Synchronous audio preprocessing using ffmpeg - runs in thread pool"""
        try:
            processed_audio_dir = os.path.join(output_dir, "processed_audio")
            chunks_dir = os.path.join(processed_audio_dir, "chunks")
            os.makedirs(chunks_dir, exist_ok=True)

            file_size_mb = os.path.getsize(input_audio_path) / 1024 / 1024
            logger.info(f"Starting audio preprocessing: {input_audio_path} ({file_size_mb:.2f} MB)")

            # Step 1: Get audio duration
            duration = self._get_duration(input_audio_path)
            logger.info(f"Audio duration: {duration:.2f} seconds")

            # Step 2: Convert to normalized mono WAV (streams to disk, low memory)
            base_name = Path(input_audio_path).stem
            cleaned_audio_path = os.path.join(processed_audio_dir, f"{base_name}_cleaned.wav")
            self._convert_and_normalize(input_audio_path, cleaned_audio_path)
            logger.info(f"Converted and normalized audio saved: {cleaned_audio_path}")

            # Step 3: Create chunks
            if duration <= self.max_chunk_sec:
                # Short audio - single chunk
                logger.info("Audio is short — saving as single chunk")
                chunk_path = os.path.join(chunks_dir, "chunk_001.wav")
                self._copy_audio(cleaned_audio_path, chunk_path)
                logger.info("Created single chunk: chunk_001.wav")
            else:
                # Long audio - smart chunking with silence detection
                logger.info("Audio is long — performing smart silence-aware chunking")
                self._smart_chunk_audio(cleaned_audio_path, chunks_dir, duration)

            logger.info(f"Audio preprocessing completed. Chunks saved in: {chunks_dir}")
            return cleaned_audio_path, chunks_dir

        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise Exception(f"Audio preprocessing failed: {str(e)}")

    def _get_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())

    def _convert_and_normalize(self, input_path: str, output_path: str):
        """
        Convert to mono WAV at target sample rate with normalization.
        Uses ffmpeg streaming - never loads full file into memory.
        """
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ac", "1",  # mono
            "-ar", str(self.target_sample_rate),  # sample rate
            "-af", "loudnorm=I=-20:TP=-1.5:LRA=11",  # normalize loudness
            "-c:a", "pcm_s16le",  # 16-bit PCM
            output_path
        ]
        logger.info("Converting and normalizing audio (streaming to disk)...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg conversion failed: {result.stderr}")

    def _copy_audio(self, input_path: str, output_path: str):
        """Copy audio file using ffmpeg (faster than Python file copy for audio)"""
        cmd = ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path]
        subprocess.run(cmd, capture_output=True, check=True)

    def _detect_silence(self, audio_path: str) -> list[tuple[float, float]]:
        """
        Detect silence ranges using ffmpeg's silencedetect filter.
        Returns list of (start, end) tuples in seconds.
        """
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-af", "silencedetect=noise=-40dB:d=0.3",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse silence_start and silence_end from stderr
        silence_ranges = []
        silence_start = None

        for line in result.stderr.split('\n'):
            if 'silence_start:' in line:
                match = re.search(r'silence_start:\s*([\d.]+)', line)
                if match:
                    silence_start = float(match.group(1))
            elif 'silence_end:' in line and silence_start is not None:
                match = re.search(r'silence_end:\s*([\d.]+)', line)
                if match:
                    silence_end = float(match.group(1))
                    silence_ranges.append((silence_start, silence_end))
                    silence_start = None

        logger.info(f"Found {len(silence_ranges)} silence ranges")
        return silence_ranges

    def _smart_chunk_audio(self, audio_path: str, output_dir: str, total_duration: float):
        """
        Split audio into chunks at silence boundaries.
        Aims for chunks between min_chunk_sec and max_chunk_sec.
        """
        silence_ranges = self._detect_silence(audio_path)

        # Convert silence ranges to potential split points (middle of each silence)
        split_points = [(s + e) / 2 for s, e in silence_ranges]

        chunks = []
        current_start = 0.0
        chunk_index = 1

        while current_start < total_duration:
            target_end = min(current_start + self.max_chunk_sec, total_duration)

            # Find best split point after min_chunk_sec
            min_end = current_start + self.min_chunk_sec
            candidates = [p for p in split_points if min_end <= p <= target_end]

            if candidates:
                # Use first silence point in valid range
                best_split = candidates[0]
            else:
                # No silence found - split at max chunk length
                best_split = target_end

            chunk_duration = best_split - current_start
            chunk_path = os.path.join(output_dir, f"chunk_{chunk_index:03d}.wav")

            # Extract chunk using ffmpeg
            self._extract_segment(audio_path, chunk_path, current_start, chunk_duration)
            logger.info(f"Created chunk_{chunk_index:03d}.wav ({chunk_duration:.2f} sec)")

            chunks.append(chunk_path)
            current_start = best_split
            chunk_index += 1

        logger.info(f"Smart chunking completed: {len(chunks)} chunks created")

    def _extract_segment(self, input_path: str, output_path: str, start: float, duration: float):
        """Extract a segment from audio file using ffmpeg"""
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg segment extraction failed: {result.stderr}")

    async def get_audio_info(self, audio_path: str) -> dict:
        """Get audio file information using ffprobe"""
        return await asyncio.to_thread(self._get_audio_info_sync, audio_path)

    def _get_audio_info_sync(self, audio_path: str) -> dict:
        """Synchronous audio info retrieval using ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration:stream=channels,sample_rate,bits_per_sample",
                "-of", "json",
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(result.stdout)

            stream = data.get("streams", [{}])[0]
            fmt = data.get("format", {})

            return {
                "duration_seconds": float(fmt.get("duration", 0)),
                "channels": int(stream.get("channels", 0)),
                "frame_rate": int(stream.get("sample_rate", 0)),
                "sample_width": int(stream.get("bits_per_sample", 16)) // 8,
                "format": audio_path.split('.')[-1].lower()
            }
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {}
