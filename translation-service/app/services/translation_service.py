import os
import asyncio
import textwrap
import time
import re
from openai import OpenAI
from pathlib import Path
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class TranslationService:
    """
    Mirrors the functionality of translate_chunks.py
    Uses OpenAI to translate English text to Japanese in chunks with retry logic
    """
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
        self.chunk_width = int(os.getenv("TRANSLATION_CHUNK_WIDTH", "3000"))
        self.max_retries = int(os.getenv("TRANSLATION_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("TRANSLATION_RETRY_DELAY", "5"))
        self.rate_limit_delay = float(os.getenv("TRANSLATION_RATE_LIMIT_DELAY", "1"))
        
        logger.info(f"Translation service initialized with model: {self.model_name}, temperature: {self.temperature}")
    
    async def translate_to_japanese(self, input_file: str, chunks_dir: str) -> str:
        """
        Translate English transcript to Japanese in chunks
        
        Args:
            input_file: Path to English transcript
            chunks_dir: Directory to save translation chunks
            
        Returns:
            str: Path to chunks directory
        """
        
        try:
            logger.info(f"Starting translation: {input_file}")
            
            # Create chunks directory
            os.makedirs(chunks_dir, exist_ok=True)
            
            # Read English transcript
            with open(input_file, 'r', encoding='utf-8') as f:
                english_transcript = f.read()
            
            # Split into chunks
            chunks = textwrap.wrap(english_transcript, width=self.chunk_width)
            logger.info(f"Split transcript into {len(chunks)} chunks")
            
            # Translation system prompt - matches your original prompt
            system_prompt = (
                "This is well known Joe and Charlie's AA workshop conversation. "
                "You are a professional translator. Translate the following English dialogue into natural, sincere spoken Japanese, as if it were a respectful and heartfelt conversation between two older men. "
                "The tone should feel like a mature discussion between two lifelong friends or seasoned individuals — warm, humble, and spoken, yet carrying dignity and emotional depth. "
                "use 僕 instead of 俺 for I phrase "
                "translate sobriety as ソーバー。 Do not translate as 清酒 "
                "Avoid stiff or formal language. Use natural phrasing that fits a spoken tone, suitable for an audiobook, podcast, or sincere AA talk. "
                "Do not change or translate the speaker labels — keep 'Speaker A:' and 'Speaker B:' exactly as they are. "
                "Do not use labels like '話者', 'スピーカー', or 'Speaker 1/2'. "
                "Preserve line breaks and paragraph structure. "
                "If the English contains informal expressions or contractions like 'don't' or 'gonna', reflect that informality naturally in Japanese."
            )
            
            # Process each chunk
            for idx, chunk in enumerate(chunks, start=1):
                chunk_file = os.path.join(chunks_dir, f"chunk_{idx:03}.txt")
                
                # Skip if chunk already exists
                if os.path.exists(chunk_file):
                    logger.info(f"✅ Chunk {idx:03} already exists. Skipping.")
                    continue
                
                logger.info(f"🔁 Translating chunk {idx}/{len(chunks)}...")
                
                # Prepare messages
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk}
                ]
                
                # Retry logic
                for attempt in range(1, self.max_retries + 1):
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            temperature=self.temperature
                        )
                        
                        content = response.choices[0].message.content.strip()
                        if not content:
                            raise ValueError("Empty response from OpenAI")
                        
                        # Clean up speaker labels (normalize any variations)
                        content = self._normalize_speaker_labels(content)
                        
                        # Add spacing between speaker changes
                        content = self._add_speaker_spacing(content)
                        
                        # Save chunk
                        with open(chunk_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Saved: {os.path.basename(chunk_file)}")
                        break
                        
                    except Exception as e:
                        logger.error(f"❌ Attempt {attempt}/{self.max_retries} failed: {e}")
                        if attempt == self.max_retries:
                            logger.error(f"💥 Giving up on chunk {idx}")
                            # Create error file to track failed chunks
                            error_file = os.path.join(chunks_dir, f"chunk_{idx:03}_ERROR.txt")
                            with open(error_file, 'w', encoding='utf-8') as f:
                                f.write(f"Translation failed after {self.max_retries} attempts\n")
                                f.write(f"Error: {str(e)}\n")
                                f.write(f"Original text:\n{chunk}")
                        else:
                            # Wait before retrying
                            await asyncio.sleep(self.retry_delay)
                
                # Small delay between chunks to respect rate limits
                await asyncio.sleep(self.rate_limit_delay)
            
            logger.info(f"Translation completed. Chunks saved in: {chunks_dir}")
            return chunks_dir
            
        except Exception as e:
            logger.error(f"Translation process failed: {e}")
            raise Exception(f"Translation failed: {str(e)}")
    
    def _normalize_speaker_labels(self, content: str) -> str:
        """Normalize speaker labels to consistent format"""
        
        # Replace various speaker label formats with standard format
        speaker_patterns = [
            (r'(話者\s*[A-Z])', r'Speaker \1'),
            (r'(スピーカー\s*[A-Z])', r'Speaker \1'), 
            (r'Speaker\s*([0-9]+)', r'Speaker \1'),
            (r'Speaker([A-Z])', r'Speaker \1')
        ]
        
        for pattern, replacement in speaker_patterns:
            content = re.sub(pattern, replacement, content)
        
        # Ensure consistent formatting: "Speaker X: "
        content = re.sub(r'(話者\s*[A-Z]|スピーカー\s*[A-Z]|Speaker\s*[A-Z0-9]+)', 
                        lambda m: f"Speaker {m.group(0)[-1]}", content)
        
        # Fix speaker labels that got corrupted
        for speaker in ['A', 'B', 'C', 'D', 'E']:
            # Handle various corrupted formats
            corrupted_patterns = [
                fr'話者\s*{speaker}',
                fr'スピーカー\s*{speaker}',
                fr'Speaker\s*{ord(speaker) - ord("A") + 1}',  # Speaker 1, Speaker 2, etc.
                fr'Speaker{speaker}'
            ]
            
            for pattern in corrupted_patterns:
                content = re.sub(pattern, f'Speaker {speaker}:', content)
        
        return content
    
    def _add_speaker_spacing(self, content: str) -> str:
        """Add spacing between different speakers"""
        
        lines = content.splitlines()
        output_lines = []
        last_speaker = None
        
        # Define speaker pattern
        speaker_pattern = r'^(Speaker [A-E]):'
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                output_lines.append('')
                continue
            
            match = re.match(speaker_pattern, line_stripped)
            if match:
                current_speaker = match.group(1)
                
                # Add double line break between different speakers
                if last_speaker and current_speaker != last_speaker:
                    output_lines.append('')  # First blank line
                    output_lines.append('')  # Second blank line
                
                last_speaker = current_speaker
            
            output_lines.append(line)
        
        return '\n'.join(output_lines)
    
    def get_translation_progress(self, chunks_dir: str) -> Dict:
        """Get translation progress information"""
        
        try:
            if not os.path.exists(chunks_dir):
                return {"progress": 0, "completed": 0, "total": 0, "errors": 0}
            
            # Count files
            all_files = os.listdir(chunks_dir)
            completed_chunks = [f for f in all_files if f.startswith('chunk_') and f.endswith('.txt') and not f.endswith('_ERROR.txt')]
            error_chunks = [f for f in all_files if f.endswith('_ERROR.txt')]
            
            # Estimate total chunks (look for highest numbered chunk)
            chunk_numbers = []
            for f in all_files:
                if f.startswith('chunk_'):
                    try:
                        num = int(f.split('_')[1].split('.')[0])
                        chunk_numbers.append(num)
                    except:
                        continue
            
            total_chunks = max(chunk_numbers) if chunk_numbers else len(completed_chunks)
            completed_count = len(completed_chunks)
            error_count = len(error_chunks)
            
            progress = (completed_count / total_chunks * 100) if total_chunks > 0 else 0
            
            return {
                "progress": round(progress, 1),
                "completed": completed_count,
                "total": total_chunks,
                "errors": error_count,
                "status": "completed" if completed_count == total_chunks else "in_progress"
            }
            
        except Exception as e:
            logger.error(f"Failed to get translation progress: {e}")
            return {"progress": 0, "completed": 0, "total": 0, "errors": 0, "error": str(e)}