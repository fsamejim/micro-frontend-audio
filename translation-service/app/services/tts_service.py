import os
import asyncio
import re
import logging
from google.cloud import texttospeech
from pydub import AudioSegment
from pathlib import Path
import json
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class TTSService:
    """
    Mirrors the functionality of multi_speaker_tts.py
    Uses Google Cloud TTS to generate Japanese audio with speaker diarization
    Accommodates rate limits, retry, and error handling
    TTS stands for Text-to-Speech
    """
    
    def __init__(self):
        # Initialize Google Cloud TTS client
        service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
        if service_account_path and os.path.exists(service_account_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
        
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS client: {e}")
            raise
        
        # Voice configurations for different speakers
        self.speaker_voices = {
            "Speaker A": {
                "name": "ja-JP-Standard-C",  # Male voice
                "gender": texttospeech.SsmlVoiceGender.MALE
            },
            "Speaker B": {
                "name": "ja-JP-Standard-D",  # Male voice (different)
                "gender": texttospeech.SsmlVoiceGender.MALE
            },
            "Speaker C": {
                "name": "ja-JP-Standard-A",  # Female voice
                "gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            "Speaker D": {
                "name": "ja-JP-Wavenet-C",  # High quality male
                "gender": texttospeech.SsmlVoiceGender.MALE
            },
            "Speaker E": {
                "name": "ja-JP-Wavenet-A",  # High quality female
                "gender": texttospeech.SsmlVoiceGender.FEMALE
            }
        }
        
        # Rate limiting
        self.requests_per_minute = int(os.getenv("TTS_REQUESTS_PER_MINUTE", "300"))
        self.request_interval = 60.0 / self.requests_per_minute  # Seconds between requests
        
        # TTS Configuration
        self.speaking_rate = float(os.getenv("TTS_SPEAKING_RATE", "1.2"))
        self.audio_bitrate = os.getenv("TTS_AUDIO_BITRATE", "192k")
        self.retry_base_delay = float(os.getenv("TTS_RETRY_BASE_DELAY", "2"))
        
    async def generate_japanese_audio(self, input_file: str, output_dir: str, merged_file: str) -> str:
        """
        Generate Japanese audio from cleaned Japanese text
        
        Args:
            input_file: Path to cleaned Japanese transcript
            output_dir: Directory to save individual audio chunks
            merged_file: Path to save final merged audio file
            
        Returns:
            str: Path to final merged audio file
        """
        
        try:
            logger.info(f"Starting Japanese audio generation: {input_file}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Parse dialogue into segments
            segments = await self._parse_dialogue_segments(input_file)
            logger.info(f"Parsed {len(segments)} dialogue segments")
            
            # Generate audio for each segment
            audio_files = []
            
            for i, segment in enumerate(segments, 1):
                speaker = segment['speaker']
                text = segment['text']
                
                # Skip empty segments
                if not text.strip():
                    continue
                
                output_file = os.path.join(output_dir, f"segment_{i:04d}_{speaker.replace(' ', '_')}.mp3")
                
                # Check if file already exists (resume capability)
                if os.path.exists(output_file):
                    logger.info(f"✅ Segment {i:04d} already exists, skipping")
                    audio_files.append(output_file)
                    continue
                
                logger.info(f"🔊 Generating audio for segment {i:04d} ({speaker})")
                
                try:
                    # Generate TTS for this segment
                    await self._generate_segment_audio(text, speaker, output_file)
                    audio_files.append(output_file)
                    
                    # Rate limiting delay
                    await asyncio.sleep(self.request_interval)
                    
                except Exception as e:
                    logger.error(f"Failed to generate segment {i:04d}: {e}")
                    # Create silence placeholder for failed segments
                    silence_file = await self._create_silence_placeholder(output_file, 2.0)
                    audio_files.append(silence_file)
            
            # Merge all audio files
            if audio_files:
                await self._merge_audio_files(audio_files, merged_file)
                logger.info(f"🎉 Japanese audio generation completed: {merged_file}")
                return merged_file
            else:
                raise Exception("No audio files were generated")
                
        except Exception as e:
            logger.error(f"Japanese audio generation failed: {e}")
            raise Exception(f"Audio generation failed: {str(e)}")
    
    async def _parse_dialogue_segments(self, input_file: str) -> List[Dict]:
        """Parse the cleaned Japanese dialogue into segments"""
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        segments = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Parse speaker lines
            speaker_match = re.match(r'^(Speaker [A-E]):\s*(.*)$', line)
            if speaker_match:
                speaker = speaker_match.group(1)
                text = speaker_match.group(2).strip()
                
                if text:  # Only add non-empty segments
                    segments.append({
                        'speaker': speaker,
                        'text': text,
                        'line_number': line_num
                    })
        
        return segments
    
    async def _generate_segment_audio(self, text: str, speaker: str, output_file: str):
        """Generate TTS audio for a single segment"""
        
        # Get voice configuration for speaker
        voice_config = self.speaker_voices.get(speaker, self.speaker_voices["Speaker A"])
        
        # Prepare TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name=voice_config["name"],
            ssml_gender=voice_config["gender"]
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=self.speaking_rate,
            pitch=0.0,
            volume_gain_db=0.0
        )
        
        # Make TTS request with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # Save audio to file
                with open(output_file, "wb") as out:
                    out.write(response.audio_content)
                
                logger.info(f"✅ Generated: {os.path.basename(output_file)}")
                return
                
            except Exception as e:
                logger.warning(f"TTS attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(self.retry_base_delay ** attempt)  # Exponential backoff
                else:
                    raise
    
    async def _create_silence_placeholder(self, output_file: str, duration_seconds: float) -> str:
        """Create a silence audio file as placeholder for failed segments"""
        
        try:
            # Create silence using pydub
            silence = AudioSegment.silent(duration=int(duration_seconds * 1000))  # milliseconds
            silence.export(output_file, format="mp3")
            logger.info(f"Created silence placeholder: {os.path.basename(output_file)}")
            return output_file
        except Exception as e:
            logger.error(f"Failed to create silence placeholder: {e}")
            raise
    
    async def _merge_audio_files(self, audio_files: List[str], output_file: str):
        """Merge multiple audio files into single file"""
        
        try:
            logger.info(f"Merging {len(audio_files)} audio files...")
            
            # Load first audio file
            combined = AudioSegment.from_mp3(audio_files[0])
            
            # Add each subsequent file with small gap
            gap_duration = 500  # 0.5 second gap between segments
            gap = AudioSegment.silent(duration=gap_duration)
            
            for audio_file in audio_files[1:]:
                try:
                    segment = AudioSegment.from_mp3(audio_file)
                    combined += gap + segment
                except Exception as e:
                    logger.warning(f"Failed to merge {audio_file}: {e}")
                    continue
            
            # Normalize volume
            combined = combined.normalize()
            
            # Export final merged file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            combined.export(output_file, format="mp3", bitrate=self.audio_bitrate)
            
            logger.info(f"✅ Merged audio saved: {output_file}")
            logger.info(f"Final audio duration: {len(combined) / 1000:.1f} seconds")
            
        except Exception as e:
            logger.error(f"Audio merging failed: {e}")
            raise
    
    def get_tts_progress(self, output_dir: str, total_segments: int) -> Dict:
        """Get TTS generation progress"""
        
        try:
            if not os.path.exists(output_dir):
                return {"progress": 0, "completed": 0, "total": total_segments}
            
            # Count completed audio files
            audio_files = [f for f in os.listdir(output_dir) if f.endswith('.mp3') and f.startswith('segment_')]
            completed_count = len(audio_files)
            
            progress = (completed_count / total_segments * 100) if total_segments > 0 else 0
            
            return {
                "progress": round(progress, 1),
                "completed": completed_count,
                "total": total_segments,
                "status": "completed" if completed_count >= total_segments else "in_progress"
            }
            
        except Exception as e:
            logger.error(f"Failed to get TTS progress: {e}")
            return {"progress": 0, "completed": 0, "total": total_segments, "error": str(e)}
    
    def get_audio_info(self, audio_file: str) -> Dict:
        """Get information about generated audio file"""
        
        try:
            if not os.path.exists(audio_file):
                return {"exists": False}
            
            audio = AudioSegment.from_mp3(audio_file)
            file_size = os.path.getsize(audio_file)
            
            return {
                "exists": True,
                "duration_seconds": len(audio) / 1000,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "channels": audio.channels,
                "frame_rate": audio.frame_rate,
                "sample_width": audio.sample_width
            }
            
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {"exists": False, "error": str(e)}