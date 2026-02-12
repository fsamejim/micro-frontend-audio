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
        
        # Japanese voice configurations for different speakers
        self.japanese_speaker_voices = {
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

        # English voice configurations for different speakers
        self.english_speaker_voices = {
            "Speaker A": {
                "name": "en-US-Standard-B",  # Male voice
                "gender": texttospeech.SsmlVoiceGender.MALE
            },
            "Speaker B": {
                "name": "en-US-Standard-D",  # Male voice (different)
                "gender": texttospeech.SsmlVoiceGender.MALE
            },
            "Speaker C": {
                "name": "en-US-Standard-C",  # Female voice
                "gender": texttospeech.SsmlVoiceGender.FEMALE
            },
            "Speaker D": {
                "name": "en-US-Wavenet-B",  # High quality male
                "gender": texttospeech.SsmlVoiceGender.MALE
            },
            "Speaker E": {
                "name": "en-US-Wavenet-C",  # High quality female
                "gender": texttospeech.SsmlVoiceGender.FEMALE
            }
        }

        # Backwards compatibility alias
        self.speaker_voices = self.japanese_speaker_voices

        # Single speaker voice configurations (for FORCE_SINGLE_SPEAKER_MODE)
        self.single_speaker_voices = {
            "ja": {
                "male": {
                    "name": "ja-JP-Wavenet-C",  # High quality Japanese male voice
                    "gender": texttospeech.SsmlVoiceGender.MALE
                },
                "female": {
                    "name": "ja-JP-Wavenet-A",  # High quality Japanese female voice
                    "gender": texttospeech.SsmlVoiceGender.FEMALE
                }
            },
            "en": {
                "male": {
                    "name": "en-US-Wavenet-B",  # High quality English male voice
                    "gender": texttospeech.SsmlVoiceGender.MALE
                },
                "female": {
                    "name": "en-US-Wavenet-C",  # High quality English female voice
                    "gender": texttospeech.SsmlVoiceGender.FEMALE
                }
            }
        }
        
        # Check environment variables for single speaker mode
        self.force_single_mode = os.getenv("FORCE_SINGLE_SPEAKER_MODE", "false").lower() == "true"
        self.single_voice_gender = os.getenv("SINGLE_SPEAKER_VOICE_GENDER", "male").lower()
        
        if self.force_single_mode:
            logger.info(f"🔒 FORCE_SINGLE_SPEAKER_MODE enabled with {self.single_voice_gender} voice")
        
        # Rate limiting
        self.requests_per_minute = int(os.getenv("TTS_REQUESTS_PER_MINUTE", "300"))
        self.request_interval = 60.0 / self.requests_per_minute  # Seconds between requests
        
        # TTS Configuration
        self.speaking_rate = float(os.getenv("TTS_SPEAKING_RATE", "1.2"))
        self.audio_bitrate = os.getenv("TTS_AUDIO_BITRATE", "192k")
        self.retry_base_delay = float(os.getenv("TTS_RETRY_BASE_DELAY", "2"))
        self.max_text_length = int(os.getenv("TTS_MAX_LENGTH", "2000"))  # Character limit per TTS call
        
    async def generate_audio(self, input_file: str, output_dir: str, merged_file: str, language_code: str = "ja") -> str:
        """
        Generate audio from cleaned transcript text

        Args:
            input_file: Path to cleaned transcript
            output_dir: Directory to save individual audio chunks
            merged_file: Path to save final merged audio file
            language_code: Target language code ("ja" or "en")

        Returns:
            str: Path to final merged audio file
        """

        try:
            lang_name = "Japanese" if language_code == "ja" else "English"
            logger.info(f"Starting {lang_name} audio generation: {input_file}")
            
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
                    await self._generate_segment_audio(text, speaker, output_file, language_code)
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
                logger.info(f"🎉 {lang_name} audio generation completed: {merged_file}")
                return merged_file
            else:
                raise Exception("No audio files were generated")

        except Exception as e:
            logger.error(f"{lang_name} audio generation failed: {e}")
            raise Exception(f"Audio generation failed: {str(e)}")

    async def generate_japanese_audio(self, input_file: str, output_dir: str, merged_file: str) -> str:
        """
        Generate Japanese audio from cleaned Japanese text (backwards compatibility wrapper)

        Args:
            input_file: Path to cleaned Japanese transcript
            output_dir: Directory to save individual audio chunks
            merged_file: Path to save final merged audio file

        Returns:
            str: Path to final merged audio file
        """
        return await self.generate_audio(input_file, output_dir, merged_file, "ja")
    
    async def _parse_dialogue_segments(self, input_file: str) -> List[Dict]:
        """Parse the dialogue into segments, handling multi-paragraph content per speaker"""

        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        segments = []
        lines = content.split('\n')

        current_speaker = None
        current_text_parts = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Check if this is a new speaker line
            speaker_match = re.match(r'^(Speaker [A-E]):\s*(.*)$', line)
            if speaker_match:
                # Save previous speaker's content if any
                if current_speaker and current_text_parts:
                    full_text = ' '.join(current_text_parts).strip()
                    if full_text:
                        segments.append({
                            "speaker": current_speaker,
                            "text": full_text
                        })

                # Start new speaker
                current_speaker = speaker_match.group(1)
                first_line_text = speaker_match.group(2).strip()
                current_text_parts = [first_line_text] if first_line_text else []
            elif line and current_speaker:
                # This is a continuation paragraph for the current speaker
                current_text_parts.append(line)

        # Don't forget the last speaker's content
        if current_speaker and current_text_parts:
            full_text = ' '.join(current_text_parts).strip()
            if full_text:
                segments.append({
                    "speaker": current_speaker,
                    "text": full_text
                })

        logger.info(f"Parsed {len(segments)} dialogue segments")
        return segments
    
    def _split_text_by_length(self, text: str, language_code: str = "ja", max_length: int = None) -> List[str]:
        """Split text into chunks at sentence boundaries, matching your working version"""
        if max_length is None:
            max_length = self.max_text_length

        chunks = []
        current_chunk = ""

        # Split by sentence endings based on language
        if language_code == "ja":
            # Japanese sentence endings
            sentence_pattern = r'(?<=[。！？\n])'
        else:
            # English sentence endings
            sentence_pattern = r'(?<=[.!?\n])\s*'

        for sentence in re.split(sentence_pattern, text):
            sentence = sentence.strip()
            if not sentence:
                continue

            test_chunk = current_chunk + (" " if current_chunk and language_code == "en" else "") + sentence
            if len(test_chunk.encode("utf-8")) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
    
    async def _generate_segment_audio(self, text: str, speaker: str, output_file: str, language_code: str = "ja"):
        """Generate TTS audio for a single segment, splitting long text if needed"""

        # Split long text into smaller chunks
        text_chunks = self._split_text_by_length(text, language_code)

        if len(text_chunks) == 1:
            # Single chunk - generate directly
            await self._generate_single_audio_chunk(text_chunks[0], speaker, output_file, language_code)
        else:
            # Multiple chunks - generate separately and merge
            logger.info(f"Splitting long text into {len(text_chunks)} chunks")
            chunk_files = []

            for i, chunk_text in enumerate(text_chunks):
                chunk_file = output_file.replace('.mp3', f'_part_{i+1}.mp3')
                await self._generate_single_audio_chunk(chunk_text, speaker, chunk_file, language_code)
                chunk_files.append(chunk_file)

            # Merge chunk files into final output
            await self._merge_audio_files(chunk_files, output_file)

            # Clean up temporary chunk files
            for chunk_file in chunk_files:
                if os.path.exists(chunk_file):
                    os.remove(chunk_file)
    
    async def _generate_single_audio_chunk(self, text: str, speaker: str, output_file: str, language_code: str = "ja"):
        """Generate TTS audio for a single text chunk"""

        # Determine language settings
        tts_language_code = "ja-JP" if language_code == "ja" else "en-US"
        speaker_voices = self.japanese_speaker_voices if language_code == "ja" else self.english_speaker_voices

        # Get voice configuration for speaker
        if self.force_single_mode:
            # Use single voice for all speakers when forced
            lang_voices = self.single_speaker_voices.get(language_code, self.single_speaker_voices["ja"])
            if self.single_voice_gender in lang_voices:
                voice_config = lang_voices[self.single_voice_gender]
            else:
                logger.warning(f"Invalid SINGLE_SPEAKER_VOICE_GENDER: {self.single_voice_gender}, defaulting to male")
                voice_config = lang_voices["male"]
        else:
            # Use different voices for different speakers (normal mode)
            voice_config = speaker_voices.get(speaker, speaker_voices["Speaker A"])

        # Prepare TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=tts_language_code,
            name=voice_config["name"],
            ssml_gender=voice_config["gender"]
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=self.speaking_rate,
            pitch=0.0,
            volume_gain_db=0.0
        )
        
        # Make TTS request with retry logic and timeout
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                    timeout=15  # 15 second timeout like your working version
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

    def list_available_voices(self, language_code: str = "ja") -> List[Dict]:
        """
        List all available voices for a given language from Google TTS API.

        Args:
            language_code: Language code ("ja" for Japanese, "en" for English)

        Returns:
            List of voice dictionaries with name, gender, and language info
        """
        try:
            # Map simple codes to full language codes for filtering
            language_mapping = {
                "ja": "ja-JP",
                "en": "en-US"
            }
            full_language_code = language_mapping.get(language_code, f"{language_code}-{language_code.upper()}")

            # Expected voice name prefixes (standard naming pattern)
            valid_prefixes = {
                "ja": ["ja-JP-"],
                "en": ["en-US-", "en-GB-", "en-AU-", "en-IN-"]
            }
            allowed_prefixes = valid_prefixes.get(language_code, [full_language_code + "-"])

            # Fetch all voices from Google TTS
            response = self.client.list_voices()

            voices = []
            skipped_voices = []
            for voice in response.voices:
                # Filter by language code
                if full_language_code in voice.language_codes:
                    # Only include voices that follow standard naming pattern
                    # This filters out special voices like "Callirrhoe" that require model specification
                    if not any(voice.name.startswith(prefix) for prefix in allowed_prefixes):
                        skipped_voices.append(voice.name)
                        continue

                    # Determine gender string
                    gender = "NEUTRAL"
                    if voice.ssml_gender == texttospeech.SsmlVoiceGender.MALE:
                        gender = "MALE"
                    elif voice.ssml_gender == texttospeech.SsmlVoiceGender.FEMALE:
                        gender = "FEMALE"

                    voices.append({
                        "name": voice.name,
                        "gender": gender,
                        "language_codes": list(voice.language_codes),
                        "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
                    })

            # Sort by voice name for consistent ordering
            voices.sort(key=lambda v: v["name"])

            logger.info(f"Found {len(voices)} voices for language {language_code} (skipped {len(skipped_voices)} non-standard voices)")
            if skipped_voices:
                logger.debug(f"Skipped voices: {skipped_voices[:10]}...")  # Log first 10 skipped

            return voices

        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            raise Exception(f"Failed to list available voices: {str(e)}")

    def validate_voice_names(self, voice_mappings: Dict[str, str], language_code: str = "ja") -> Dict[str, str]:
        """
        Validate that all voice names in the mappings are available.

        Args:
            voice_mappings: Dictionary mapping speaker names to voice names
            language_code: Target language code

        Returns:
            Dictionary of invalid voices: {speaker: voice_name}
        """
        if not voice_mappings:
            return {}

        try:
            available_voices = self.list_available_voices(language_code)
            available_voice_names = {v["name"] for v in available_voices}

            invalid_voices = {}
            for speaker, voice_name in voice_mappings.items():
                if voice_name and voice_name not in available_voice_names:
                    invalid_voices[speaker] = voice_name

            return invalid_voices
        except Exception as e:
            logger.warning(f"Could not validate voices: {e}")
            return {}

    def _get_voice_gender_from_api(self, voice_name: str) -> texttospeech.SsmlVoiceGender:
        """
        Get the actual gender for a voice from the Google TTS API.

        Args:
            voice_name: The voice name (e.g., "ja-JP-Neural2-B")

        Returns:
            The SsmlVoiceGender enum value
        """
        try:
            # Fetch all voices from Google TTS
            response = self.client.list_voices()

            for voice in response.voices:
                if voice.name == voice_name:
                    logger.info(f"Found voice {voice_name} with gender {voice.ssml_gender}")
                    return voice.ssml_gender

            # Voice not found, default to NEUTRAL
            logger.warning(f"Voice {voice_name} not found in API, defaulting to NEUTRAL")
            return texttospeech.SsmlVoiceGender.NEUTRAL

        except Exception as e:
            logger.error(f"Failed to get voice gender from API: {e}")
            # Default to NEUTRAL on error
            return texttospeech.SsmlVoiceGender.NEUTRAL

    async def generate_audio_with_custom_voices(
        self,
        input_file: str,
        voice_mappings: Dict[str, str],
        speaking_rate: float,
        output_dir: str,
        output_file: str,
        language_code: str = "ja"
    ) -> str:
        """
        Generate audio with custom voice mappings for each speaker.

        Args:
            input_file: Path to cleaned transcript file
            voice_mappings: Dictionary mapping speaker names to voice names
                           e.g., {"Speaker A": "ja-JP-Wavenet-B", "Speaker B": "ja-JP-Standard-C"}
            speaking_rate: Speaking rate (0.5 to 2.0)
            output_dir: Directory to save individual audio segments
            output_file: Path to save final merged audio file
            language_code: Target language code ("ja" or "en")

        Returns:
            str: Path to final merged audio file
        """
        try:
            lang_name = "Japanese" if language_code == "ja" else "English"
            logger.info(f"Starting custom {lang_name} audio generation with custom voices")
            logger.info(f"Voice mappings: {voice_mappings}")
            logger.info(f"Speaking rate: {speaking_rate}")

            # Log voice validation (non-blocking - Google TTS will handle errors)
            # Skip strict validation as newer voice types (Chirp3-HD, etc.) may not match old patterns
            logger.info(f"Voice mappings provided: {voice_mappings}")

            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Parse dialogue into segments
            segments = await self._parse_dialogue_segments(input_file)
            logger.info(f"Parsed {len(segments)} dialogue segments")

            if not segments:
                raise Exception("No dialogue segments found in transcript")

            # Generate audio for each segment with custom voices
            audio_files = []
            failed_segments = []
            tts_language_code = "ja-JP" if language_code == "ja" else "en-US"

            # Build effective voice mapping (with defaults)
            speaker_voices = self.japanese_speaker_voices if language_code == "ja" else self.english_speaker_voices
            effective_voice_mapping = {}

            for i, segment in enumerate(segments, 1):
                speaker = segment['speaker']
                text = segment['text']

                # Skip empty segments
                if not text.strip():
                    continue

                segment_output_file = os.path.join(output_dir, f"segment_{i:04d}_{speaker.replace(' ', '_')}.mp3")

                # Get custom voice for this speaker, or use default
                voice_name = voice_mappings.get(speaker) if voice_mappings else None

                # If voice is not set, use default
                if not voice_name:
                    voice_config = speaker_voices.get(speaker, speaker_voices["Speaker A"])
                    voice_name = voice_config["name"]

                # Track effective voice mapping
                if speaker not in effective_voice_mapping:
                    effective_voice_mapping[speaker] = voice_name

                logger.info(f"🔊 Segment {i:04d} | {speaker} | Voice: {voice_name} | Text: {text[:50]}...")

                try:
                    # Detect accent mixing (voice language different from transcript language)
                    voice_lang = voice_name.split('-')[0] if voice_name and '-' in voice_name else None
                    transcript_lang = language_code[:2] if language_code else None
                    is_accent_mixing = voice_lang and transcript_lang and voice_lang != transcript_lang

                    # Use smaller chunks for accent mixing (cross-language voices have stricter limits)
                    if is_accent_mixing:
                        logger.info(f"Accent mixing detected: {voice_lang} voice with {transcript_lang} text - using 500 char chunks")
                        max_chunk_length = 500
                    else:
                        max_chunk_length = self.max_text_length

                    # Split long text into chunks if needed
                    text_chunks = self._split_text_by_length(text, language_code, max_chunk_length)
                    logger.info(f"Split text into {len(text_chunks)} chunks (max_length={max_chunk_length})")
                    if len(text_chunks) > 1:
                        for idx, chunk in enumerate(text_chunks):
                            logger.info(f"  Chunk {idx+1}: {len(chunk)} chars, starts with: {chunk[:50]}...")

                    if len(text_chunks) == 1:
                        # Single chunk - generate directly
                        await self._generate_custom_audio_chunk(
                            text_chunks[0], voice_name, segment_output_file,
                            tts_language_code, speaking_rate
                        )
                    else:
                        # Multiple chunks - generate separately and merge
                        logger.info(f"Splitting long text into {len(text_chunks)} chunks")
                        chunk_files = []

                        for j, chunk_text in enumerate(text_chunks):
                            chunk_file = segment_output_file.replace('.mp3', f'_part_{j+1}.mp3')
                            await self._generate_custom_audio_chunk(
                                chunk_text, voice_name, chunk_file,
                                tts_language_code, speaking_rate
                            )
                            chunk_files.append(chunk_file)

                        # Merge chunk files
                        await self._merge_audio_files(chunk_files, segment_output_file)

                        # Clean up temporary chunk files
                        for chunk_file in chunk_files:
                            if os.path.exists(chunk_file):
                                os.remove(chunk_file)

                    # Verify file was created
                    if os.path.exists(segment_output_file) and os.path.getsize(segment_output_file) > 100:
                        audio_files.append(segment_output_file)
                        logger.info(f"✅ Segment {i:04d} generated successfully")
                    else:
                        raise Exception("Generated file is empty or missing")

                    # Rate limiting delay
                    await asyncio.sleep(self.request_interval)

                except Exception as e:
                    logger.error(f"❌ Failed to generate segment {i:04d} ({speaker}, voice: {voice_name}): {e}")
                    failed_segments.append({
                        "segment": i,
                        "speaker": speaker,
                        "voice": voice_name,
                        "error": str(e)
                    })
                    # Create silence placeholder for failed segments
                    silence_file = await self._create_silence_placeholder(segment_output_file, 2.0)
                    audio_files.append(silence_file)

            # Log summary
            logger.info(f"=" * 50)
            logger.info(f"GENERATION SUMMARY")
            logger.info(f"=" * 50)
            logger.info(f"Total segments: {len(segments)}")
            logger.info(f"Successful: {len(segments) - len(failed_segments)}")
            logger.info(f"Failed: {len(failed_segments)}")
            logger.info(f"Effective voice mapping: {effective_voice_mapping}")

            if failed_segments:
                logger.error(f"Failed segments details:")
                for fs in failed_segments:
                    logger.error(f"  - Segment {fs['segment']} ({fs['speaker']}): {fs['error']}")

            # Check if ALL segments failed
            successful_count = len(segments) - len(failed_segments)
            if successful_count == 0 and len(segments) > 0:
                # All segments failed - this is a critical error
                error_details = "; ".join([f"{fs['speaker']}: {fs['error']}" for fs in failed_segments[:3]])
                raise Exception(f"All {len(segments)} segments failed to generate. Errors: {error_details}")

            # Merge all audio files
            if audio_files:
                await self._merge_audio_files(audio_files, output_file)
                logger.info(f"🎉 Custom {lang_name} audio generation completed: {output_file}")

                # Raise warning if there were failures
                if failed_segments:
                    failed_speakers = list(set(fs['speaker'] for fs in failed_segments))
                    logger.warning(f"⚠️ Audio generated with {len(failed_segments)} failed segments (speakers: {failed_speakers})")

                # Return result with metadata
                return {
                    "output_file": output_file,
                    "total_segments": len(segments),
                    "successful_segments": successful_count,
                    "failed_segments": failed_segments,
                    "effective_voice_mapping": effective_voice_mapping
                }
            else:
                raise Exception("No audio files were generated")

        except Exception as e:
            logger.error(f"Custom audio generation failed: {e}")
            raise Exception(f"Custom audio generation failed: {str(e)}")

    async def _generate_custom_audio_chunk(
        self,
        text: str,
        voice_name: str,
        output_file: str,
        language_code: str,
        speaking_rate: float
    ):
        """Generate TTS audio for a single text chunk with custom voice and rate"""

        # Extract language code from voice name (e.g., "ja-JP-Neural2-B" -> "ja-JP")
        # This ensures the language code matches the voice
        voice_language_code = language_code  # default fallback
        if voice_name:
            parts = voice_name.split('-')
            if len(parts) >= 2:
                # Handle patterns like "ja-JP-...", "en-US-...", "en-GB-..."
                potential_lang = f"{parts[0]}-{parts[1]}"
                if potential_lang in ['ja-JP', 'en-US', 'en-GB', 'en-AU', 'en-IN']:
                    voice_language_code = potential_lang

        logger.info(f"Generating audio chunk: voice={voice_name}, voice_lang={voice_language_code}, target_lang={language_code}, rate={speaking_rate}")
        logger.info(f"Text preview: {text[:100]}...")

        # Determine voice type for retry logic and gender selection
        # Only Wavenet and Standard voices support NEUTRAL gender
        supports_neutral = any(vtype in voice_name for vtype in ['Wavenet', 'Standard'])
        is_legacy_voice = supports_neutral  # For retry logic compatibility

        # Determine gender - Neural2, Studio, Chirp, etc. require actual gender
        if supports_neutral:
            # Wavenet/Standard support NEUTRAL gender
            gender = texttospeech.SsmlVoiceGender.NEUTRAL
            logger.info(f"Using NEUTRAL gender for {voice_name}")
        else:
            # Get actual gender from voice list API for Neural2, Studio, Chirp, etc.
            gender = self._get_voice_gender_from_api(voice_name)
            logger.info(f"Using actual gender from API for {voice_name}: {gender}")

        # Prepare TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_language_code,  # Use language from voice name
            name=voice_name,
            ssml_gender=gender
        )

        # Make TTS request with retry logic
        max_retries = 3
        current_rate = speaking_rate

        for attempt in range(max_retries):
            try:
                # Update audio config with current rate (might change on retry)
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=current_rate,
                    pitch=0.0,
                    volume_gain_db=0.0
                )

                logger.info(f"TTS request attempt {attempt + 1}/{max_retries} for voice {voice_name} (rate={current_rate})")
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                    timeout=30  # Increased timeout for newer voices
                )

                # Verify we got audio content
                if not response.audio_content or len(response.audio_content) < 100:
                    raise Exception(f"Empty or too small audio response ({len(response.audio_content) if response.audio_content else 0} bytes)")

                # Save audio to file
                with open(output_file, "wb") as out:
                    out.write(response.audio_content)

                file_size = os.path.getsize(output_file)
                logger.info(f"✅ Generated: {os.path.basename(output_file)} ({file_size} bytes)")
                return

            except Exception as e:
                logger.error(f"TTS attempt {attempt + 1}/{max_retries} failed for voice {voice_name}: {e}")

                # On second attempt, try with default speaking rate (some voices don't support custom rates)
                if attempt == 0 and current_rate != 1.0 and not is_legacy_voice:
                    logger.warning(f"Retrying with default speaking rate (1.0) for newer voice {voice_name}")
                    current_rate = 1.0

                if attempt < max_retries - 1:
                    await asyncio.sleep(self.retry_base_delay ** attempt)
                else:
                    logger.error(f"All TTS attempts failed for voice {voice_name}")
                    raise