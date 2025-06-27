import os
import asyncio
import assemblyai as aai
from pathlib import Path
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Mirrors the functionality of assemblescript.py
    Uses AssemblyAI to transcribe audio chunks with speaker diarization
    This is the service that extract the text from the audio file
    """
    
    def __init__(self):
        # Set AssemblyAI API key from environment
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise ValueError("ASSEMBLYAI_API_KEY environment variable is required")
        
        aai.settings.api_key = api_key
        
        # Configure model and delays
        model_name = os.getenv("ASSEMBLYAI_MODEL", "best")
        self.speech_model = aai.SpeechModel.best if model_name == "best" else aai.SpeechModel.nano
        self.rate_limit_delay = float(os.getenv("TRANSCRIPTION_RATE_LIMIT_DELAY", "1"))
        
        logger.info(f"AssemblyAI service initialized with model: {model_name}")
    
    async def transcribe_chunks(self, chunks_dir: str, output_file: str) -> str:
        """
        Transcribe all audio chunks and combine into single transcript
        
        Args:
            chunks_dir: Directory containing audio chunks
            output_file: Path to save the combined transcript
            
        Returns:
            str: Path to the transcript file
        """
        
        try:
            logger.info(f"Starting transcription of chunks in: {chunks_dir}")
            
            # Get all chunk files and sort them
            chunk_files = sorted([
                f for f in os.listdir(chunks_dir) 
                if f.endswith(('.wav', '.mp3', '.m4a'))
            ])
            
            if not chunk_files:
                raise ValueError(f"No audio chunks found in {chunks_dir}")
            
            logger.info(f"Found {len(chunk_files)} chunks to transcribe")
            
            # Configure transcription with speaker diarization
            config = aai.TranscriptionConfig(
                speech_model=self.speech_model,
                speaker_labels=True
            )
            
            transcriber = aai.Transcriber(config=config)
            all_transcripts = []
            
            # Process each chunk
            for i, chunk_file in enumerate(chunk_files, 1):
                chunk_path = os.path.join(chunks_dir, chunk_file)
                logger.info(f"Transcribing chunk {i}/{len(chunk_files)}: {chunk_file}")
                
                try:
                    # Transcribe the chunk
                    transcript = transcriber.transcribe(chunk_path)
                    
                    # Check for errors
                    if transcript.status == "error":
                        logger.error(f"Transcription failed for {chunk_file}: {transcript.error}")
                        continue
                    
                    # Extract utterances with speaker labels
                    chunk_transcript = []
                    if hasattr(transcript, 'utterances') and transcript.utterances:
                        for utterance in transcript.utterances:
                            speaker_label = f"Speaker {utterance.speaker}"
                            chunk_transcript.append(f"{speaker_label}: {utterance.text}")
                    else:
                        # Fallback if no speaker diarization
                        chunk_transcript.append(f"Speaker A: {transcript.text}")
                    
                    all_transcripts.extend(chunk_transcript)
                    logger.info(f"Successfully transcribed chunk {i}/{len(chunk_files)}")
                    
                    # Small delay to respect API rate limits
                    await asyncio.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Failed to transcribe chunk {chunk_file}: {e}")
                    continue
            
            if not all_transcripts:
                raise ValueError("No successful transcriptions produced")
            
            # Save combined transcript
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_transcripts))
            
            logger.info(f"Combined transcript saved: {output_file}")
            logger.info(f"Total transcript lines: {len(all_transcripts)}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Transcription process failed: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    async def transcribe_single_file(self, audio_path: str, output_file: str) -> str:
        """
        Transcribe a single audio file (for smaller files)
        
        Args:
            audio_path: Path to audio file
            output_file: Path to save transcript
            
        Returns:
            str: Path to the transcript file
        """
        
        try:
            logger.info(f"Transcribing single file: {audio_path}")
            
            # Configure transcription
            config = aai.TranscriptionConfig(
                speech_model=self.speech_model,
                speaker_labels=True
            )
            
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_path)
            
            # Check for errors
            if transcript.status == "error":
                raise Exception(f"Transcription failed: {transcript.error}")
            
            # Format with speaker labels
            transcript_lines = []
            if hasattr(transcript, 'utterances') and transcript.utterances:
                for utterance in transcript.utterances:
                    speaker_label = f"Speaker {utterance.speaker}"
                    transcript_lines.append(f"{speaker_label}: {utterance.text}")
            else:
                # Fallback if no speaker diarization
                transcript_lines.append(f"Speaker A: {transcript.text}")
            
            # Save transcript
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(transcript_lines))
            
            logger.info(f"Transcript saved: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Single file transcription failed: {e}")
            raise Exception(f"Transcription failed: {str(e)}")
    
    def get_transcription_info(self, transcript_path: str) -> Dict:
        """Get information about a transcript file"""
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Count speakers
            speakers = set()
            for line in lines:
                if line.strip().startswith('Speaker'):
                    speaker = line.split(':')[0].strip()
                    speakers.add(speaker)
            
            return {
                "total_lines": len(lines),
                "speakers_found": list(speakers),
                "speaker_count": len(speakers)
            }
        except Exception as e:
            logger.error(f"Failed to get transcript info: {e}")
            return {}