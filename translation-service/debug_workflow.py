#!/usr/bin/env python3
"""
Debug Workflow Script for Translation Service

This script allows you to test each step of the translation workflow independently.
Perfect for debugging issues and understanding the pipeline.

Usage:
    python debug_workflow.py --step all --input test-data/joe-charlie-first-5-minutes.mp3
    python debug_workflow.py --step 1 --input test-data/joe-charlie-first-5-minutes.mp3
    python debug_workflow.py --step 2 --input debug_output/step1_preprocessing/processed_audio/chunks
    python debug_workflow.py --step 3 --input debug_output/step2_transcription/raw_transcript.txt
    python debug_workflow.py --step 4 --input debug_output/step3_formatting/formatted_transcript.txt
    python debug_workflow.py --step 5 --input debug_output/step4_translation/
    python debug_workflow.py --step 6 --input debug_output/step5_merging/merged_japanese.txt
    python debug_workflow.py --step 7 --input debug_output/step6_cleaning/clean_japanese.txt
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import all services
from app.services.audio_preprocessing_service import AudioPreprocessingService
from app.services.transcription_service import TranscriptionService
from app.services.text_formatting_service import TextFormattingService
from app.services.translation_service import TranslationService
from app.services.chunk_merging_service import ChunkMergingService
from app.services.text_cleaning_service import TextCleaningService
from app.services.tts_service import TTSService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugWorkflow:
    def __init__(self, debug_dir: str = "debug_output"):
        self.debug_dir = debug_dir
        self.job_id = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.setup_directories()
    
    def setup_directories(self):
        """Create debug output directories"""
        dirs = [
            f"{self.debug_dir}/step1_preprocessing",
            f"{self.debug_dir}/step2_transcription", 
            f"{self.debug_dir}/step3_formatting",
            f"{self.debug_dir}/step4_translation",
            f"{self.debug_dir}/step5_merging",
            f"{self.debug_dir}/step6_cleaning",
            f"{self.debug_dir}/step7_tts",
            f"{self.debug_dir}/logs"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info(f"Debug directories created in: {self.debug_dir}")
    
    async def step1_audio_preprocessing(self, input_audio: str) -> tuple[str, str]:
        """Step 1: Audio Preprocessing - Clean and chunk audio"""
        
        logger.info("=" * 60)
        logger.info("STEP 1: AUDIO PREPROCESSING")
        logger.info("=" * 60)
        
        if not os.path.exists(input_audio):
            raise FileNotFoundError(f"Input audio file not found: {input_audio}")
        
        try:
            service = AudioPreprocessingService()
            output_dir = f"{self.debug_dir}/step1_preprocessing"
            
            # Get audio info first
            audio_info = await service.get_audio_info(input_audio)
            logger.info(f"Input audio info: {audio_info}")
            
            # Preprocess audio
            cleaned_path, chunks_dir = await service.preprocess_audio(input_audio, output_dir)
            
            # Log results
            logger.info(f"✓ Cleaned audio: {cleaned_path}")
            logger.info(f"✓ Chunks directory: {chunks_dir}")
            
            # Count chunks
            chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.wav')]
            logger.info(f"✓ Created {len(chunk_files)} audio chunks")
            
            return cleaned_path, chunks_dir
            
        except Exception as e:
            logger.error(f"✗ Step 1 failed: {e}")
            raise
    
    async def step2_transcription(self, chunks_dir: str) -> str:
        """Step 2: Transcription - Convert audio to text with speaker labels"""
        
        logger.info("=" * 60)
        logger.info("STEP 2: TRANSCRIPTION")
        logger.info("=" * 60)
        
        if not os.path.exists(chunks_dir):
            raise FileNotFoundError(f"Chunks directory not found: {chunks_dir}")
        
        try:
            service = TranscriptionService()
            output_file = f"{self.debug_dir}/step2_transcription/raw_transcript.txt"
            
            # Transcribe chunks
            transcript_path = await service.transcribe_chunks(chunks_dir, output_file)
            
            # Get transcript info
            transcript_info = service.get_transcription_info(transcript_path)
            logger.info(f"✓ Transcript info: {transcript_info}")
            
            # Show sample lines
            with open(transcript_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]  # First 5 lines
            
            logger.info("✓ Sample transcript lines:")
            for i, line in enumerate(lines, 1):
                logger.info(f"  {i}: {line.strip()}")
            
            return transcript_path
            
        except Exception as e:
            logger.error(f"✗ Step 2 failed: {e}")
            raise
    
    async def step3_text_formatting(self, raw_transcript: str) -> str:
        """Step 3: Text Formatting - Format transcript with proper speaker tags"""
        
        logger.info("=" * 60)
        logger.info("STEP 3: TEXT FORMATTING")
        logger.info("=" * 60)
        
        if not os.path.exists(raw_transcript):
            raise FileNotFoundError(f"Raw transcript not found: {raw_transcript}")
        
        try:
            service = TextFormattingService()
            output_file = f"{self.debug_dir}/step3_formatting/formatted_transcript.txt"
            
            # Format transcript
            formatted_path = await service.format_transcript(raw_transcript, output_file)
            
            # Show sample formatted lines
            with open(formatted_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
            
            logger.info("✓ Sample formatted lines:")
            for i, line in enumerate(lines, 1):
                logger.info(f"  {i}: {line.strip()}")
            
            return formatted_path
            
        except Exception as e:
            logger.error(f"✗ Step 3 failed: {e}")
            raise
    
    async def step4_translation(self, formatted_transcript: str) -> str:
        """Step 4: Translation - Translate English to Japanese in chunks"""
        
        logger.info("=" * 60)
        logger.info("STEP 4: TRANSLATION TO JAPANESE")
        logger.info("=" * 60)
        
        if not os.path.exists(formatted_transcript):
            raise FileNotFoundError(f"Formatted transcript not found: {formatted_transcript}")
        
        try:
            service = TranslationService()
            output_dir = f"{self.debug_dir}/step4_translation"
            
            # Translate to Japanese
            chunks_dir = await service.translate_to_japanese(formatted_transcript, output_dir)
            
            # Show translation chunks
            chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.txt')]
            logger.info(f"✓ Created {len(chunk_files)} translation chunks")
            
            # Show sample from first chunk
            if chunk_files:
                first_chunk = os.path.join(chunks_dir, sorted(chunk_files)[0])
                with open(first_chunk, 'r', encoding='utf-8') as f:
                    content = f.read()[:200]  # First 200 chars
                logger.info(f"✓ Sample translation: {content}...")
            
            return chunks_dir
            
        except Exception as e:
            logger.error(f"✗ Step 4 failed: {e}")
            raise
    
    async def step5_chunk_merging(self, translation_chunks_dir: str) -> str:
        """Step 5: Chunk Merging - Combine translation chunks"""
        
        logger.info("=" * 60)
        logger.info("STEP 5: CHUNK MERGING")
        logger.info("=" * 60)
        
        if not os.path.exists(translation_chunks_dir):
            raise FileNotFoundError(f"Translation chunks directory not found: {translation_chunks_dir}")
        
        try:
            service = ChunkMergingService()
            output_file = f"{self.debug_dir}/step5_merging/merged_japanese.txt"
            
            # Merge chunks
            merged_path = await service.merge_translation_chunks(translation_chunks_dir, output_file)
            
            # Show file info
            with open(merged_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            logger.info(f"✓ Merged file: {len(lines)} lines, {len(content)} characters")
            logger.info(f"✓ Sample merged content: {content[:300]}...")
            
            return merged_path
            
        except Exception as e:
            logger.error(f"✗ Step 5 failed: {e}")
            raise
    
    async def step6_text_cleaning(self, merged_japanese: str) -> str:
        """Step 6: Text Cleaning - Clean Japanese text artifacts"""
        
        logger.info("=" * 60)
        logger.info("STEP 6: TEXT CLEANING")
        logger.info("=" * 60)
        
        if not os.path.exists(merged_japanese):
            raise FileNotFoundError(f"Merged Japanese text not found: {merged_japanese}")
        
        try:
            service = TextCleaningService()
            output_file = f"{self.debug_dir}/step6_cleaning/clean_japanese.txt"
            
            # Clean text
            clean_path = await service.clean_japanese_text(merged_japanese, output_file)
            
            # Show cleaning results
            with open(clean_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            logger.info(f"✓ Cleaned file: {len(lines)} lines, {len(content)} characters")
            logger.info(f"✓ Sample cleaned content: {content[:300]}...")
            
            return clean_path
            
        except Exception as e:
            logger.error(f"✗ Step 6 failed: {e}")
            raise
    
    async def step7_tts(self, clean_japanese: str) -> str:
        """Step 7: Text-to-Speech - Generate Japanese audio"""
        
        logger.info("=" * 60)
        logger.info("STEP 7: TEXT-TO-SPEECH")
        logger.info("=" * 60)
        
        if not os.path.exists(clean_japanese):
            raise FileNotFoundError(f"Clean Japanese text not found: {clean_japanese}")
        
        try:
            service = TTSService()
            audio_dir = f"{self.debug_dir}/step7_tts/audio_segments"
            final_audio = f"{self.debug_dir}/step7_tts/final_japanese_audio.mp3"
            
            # Generate audio
            await service.generate_japanese_audio(clean_japanese, audio_dir, final_audio)
            
            # Show results
            if os.path.exists(final_audio):
                file_size = os.path.getsize(final_audio) / (1024 * 1024)  # MB
                logger.info(f"✓ Final audio: {final_audio} ({file_size:.2f} MB)")
            
            # Count audio segments
            if os.path.exists(audio_dir):
                audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
                logger.info(f"✓ Generated {len(audio_files)} audio segments")
            
            return final_audio
            
        except Exception as e:
            logger.error(f"✗ Step 7 failed: {e}")
            raise
    
    async def run_all_steps(self, input_audio: str):
        """Run all steps in sequence"""
        
        logger.info("🚀 Starting complete workflow debug")
        logger.info(f"Input audio: {input_audio}")
        logger.info(f"Debug output: {self.debug_dir}")
        
        try:
            # Step 1: Audio Preprocessing
            cleaned_audio, chunks_dir = await self.step1_audio_preprocessing(input_audio)
            
            # Step 2: Transcription
            raw_transcript = await self.step2_transcription(chunks_dir)
            
            # Step 3: Text Formatting
            formatted_transcript = await self.step3_text_formatting(raw_transcript)
            
            # Step 4: Translation
            translation_chunks = await self.step4_translation(formatted_transcript)
            
            # Step 5: Chunk Merging
            merged_japanese = await self.step5_chunk_merging(translation_chunks)
            
            # Step 6: Text Cleaning
            clean_japanese = await self.step6_text_cleaning(merged_japanese)
            
            # Step 7: TTS
            final_audio = await self.step7_tts(clean_japanese)
            
            logger.info("=" * 60)
            logger.info("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"Final Japanese audio: {final_audio}")
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Debug Translation Service Workflow')
    parser.add_argument('--step', choices=['1', '2', '3', '4', '5', '6', '7', 'all'], 
                       required=True, help='Step to run')
    parser.add_argument('--input', required=True, help='Input file/directory for the step')
    parser.add_argument('--debug-dir', default='debug_output', help='Debug output directory')
    
    args = parser.parse_args()
    
    # Check environment variables
    required_env_vars = ['ASSEMBLYAI_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars and args.step in ['2', '4', 'all']:
        logger.error(f"Missing environment variables: {missing_vars}")
        logger.info("Set them in your shell or create a .env file")
        return 1
    
    # Create debug workflow
    workflow = DebugWorkflow(args.debug_dir)
    
    async def run_step():
        try:
            if args.step == '1':
                await workflow.step1_audio_preprocessing(args.input)
            elif args.step == '2':
                await workflow.step2_transcription(args.input)
            elif args.step == '3':
                await workflow.step3_text_formatting(args.input)
            elif args.step == '4':
                await workflow.step4_translation(args.input)
            elif args.step == '5':
                await workflow.step5_chunk_merging(args.input)
            elif args.step == '6':
                await workflow.step6_text_cleaning(args.input)
            elif args.step == '7':
                await workflow.step7_tts(args.input)
            elif args.step == 'all':
                await workflow.run_all_steps(args.input)
            
            logger.info("✅ Debug step completed successfully!")
            return 0
            
        except Exception as e:
            logger.error(f"❌ Debug step failed: {e}")
            return 1
    
    # Run the async function
    return asyncio.run(run_step())

if __name__ == "__main__":
    sys.exit(main())