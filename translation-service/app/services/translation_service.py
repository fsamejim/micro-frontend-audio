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
        self.max_retries = int(os.getenv("TRANSLATION_MAX_RETRIES", "4"))  # Match base code
        self.retry_delay = float(os.getenv("TRANSLATION_RETRY_DELAY", "5"))
        self.rate_limit_delay = float(os.getenv("TRANSLATION_RATE_LIMIT_DELAY", "1"))
        self.enable_tag_normalization = os.getenv("ENABLE_TAG_NORMALIZATION", "true").lower() == "true"
        
        # Speaker configuration from base code
        self.speaker_ids = ["A", "B", "C", "D", "E"]
        self.speaker_pattern = "|".join([f"Speaker {s}" for s in self.speaker_ids])
        
        logger.info(f"Translation service initialized with model: {self.model_name}, temperature: {self.temperature}")
        logger.info(f"Tag normalization enabled: {self.enable_tag_normalization}")
    
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
            
            # Split into chunks using speaker-aware chunking
            chunks = self._split_text_by_speakers(english_transcript)
            logger.info(f"Split transcript into {len(chunks)} chunks")
            
            # Translation system prompt - matches your working version
            system_prompt = textwrap.dedent("""\
                    This is the well-known Joe and Charlie's AA workshop conversation.
                    You are a professional translator. Translate the following English dialogue into natural, sincere spoken Japanese, as if it were a respectful and heartfelt conversation between two older men. 
                    The tone should feel like a mature discussion between two lifelong friends or seasoned individuals — warm, humble, and spoken, yet carrying dignity and emotional depth. 
                    Avoid stiff or formal language. Use natural phrasing that fits a spoken tone, suitable for an audiobook, podcast, or sincere AA talk. 
                    Use 私 instead of 俺. Translate 'sobriety' as ソーバー (not 清酒). Translate ALCOHOLICS ANONYMOUS as アルコホーリクス・アノニマス. Translate Big Book as ビッグブック. 
                    Do not change or translate the speaker labels — keep 'Speaker A:' and 'Speaker B:' exactly as they are. 
                    Do not use labels like '話者', 'スピーカー', or 'Speaker 1/2'. 
                    Translate ALL English into natural spoken Japanese. Do not leave any part in English. Even if the sentence sounds like a quote, a slogan, or an AA motto, translate it. Do not preserve any English phrases. Keep the speaker labels exactly as they are (e.g., 'Speaker A:', 'Speaker B:').
                    Do not add or infer speaker tags if they are missing. Keep all line breaks and structure as-is.
                """)
            
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
                
                # Enhanced retry logic with exponential backoff (from base code)
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
                        
                        # Enhanced tag normalization (matching base code logic)
                        if self.enable_tag_normalization:
                            content = self._normalize_speaker_labels(content)
                            content = self._add_speaker_spacing(content)
                        else:
                            # Basic cleanup without normalization
                            content = self._add_speaker_spacing(content)
                        
                        # Save chunk
                        with open(chunk_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Saved: {os.path.basename(chunk_file)}")
                        
                        # Rate limit delay after successful translation
                        await asyncio.sleep(self.rate_limit_delay)
                        break
                        
                    except Exception as e:
                        logger.error(f"❌ Attempt {attempt}/{self.max_retries} failed on chunk {idx}: {e}")
                        if attempt == self.max_retries:
                            logger.error(f"💥 Giving up on chunk {idx} after {self.max_retries} attempts")
                            # Create detailed error file
                            error_file = os.path.join(chunks_dir, f"chunk_{idx:03}_ERROR.txt")
                            with open(error_file, 'w', encoding='utf-8') as f:
                                f.write(f"Translation failed after {self.max_retries} attempts\n")
                                f.write(f"Last error: {str(e)}\n")
                                f.write(f"Chunk length: {len(chunk)} characters\n")
                                f.write(f"Model: {self.model_name}\n")
                                f.write(f"Temperature: {self.temperature}\n")
                                f.write(f"\nOriginal text:\n{chunk}")
                            break
                        else:
                            # Exponential backoff (matching base code)
                            # attempt=1: 5*1=5s, attempt=2: 5*1.5=7.5s, attempt=3: 5*2.25=11.25s, attempt=4: 5*3.375≈16.9s
                            delay = self.retry_delay * (1.5 ** (attempt - 1))
                            logger.info(f"⏳ Waiting {delay:.1f} seconds before retry {attempt + 1}...")
                            await asyncio.sleep(delay)
                
                # Rate limit delay is now handled in success case above
            
            logger.info(f"Translation completed. Chunks saved in: {chunks_dir}")
            return chunks_dir
            
        except Exception as e:
            logger.error(f"Translation process failed: {e}")
            raise Exception(f"Translation failed: {str(e)}")
    
    def _normalize_speaker_labels(self, content: str) -> str:
        """Enhanced speaker label normalization (matching base code logic)"""
        
        # First pass: Fix common Japanese translations and format issues (from base code)
        for speaker in self.speaker_ids:
            # Handle various formats that OpenAI might produce
            patterns_to_fix = [
                # Japanese translations
                fr"話者\s*{speaker}",
                fr"スピーカー\s*{speaker}", 
                # Numeric speaker labels (Speaker 1, Speaker 2, etc.)
                fr"Speaker\s*{ord(speaker) - ord('A') + 1}",
                # Missing space/colon
                fr"Speaker{speaker}",
                # Extra spaces
                fr"Speaker\s+{speaker}"
            ]
            
            for pattern in patterns_to_fix:
                content = re.sub(pattern, f"Speaker {speaker}:", content, flags=re.IGNORECASE)
        
        return content
    
    def _add_speaker_spacing(self, content: str) -> str:
        """Enhanced speaker spacing (matching base code logic)"""
        
        lines = content.splitlines()
        output_lines = []
        last_speaker = None
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for speaker line using the pattern from base code
            match = re.match(fr"^({self.speaker_pattern}):", line_stripped)
            if match:
                current_speaker = match.group(1)
                
                # Add spacing between different speakers (base code logic)
                if last_speaker and current_speaker != last_speaker:
                    output_lines.append("")  # First blank line
                    output_lines.append("")  # Second blank line
                
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
    
    def _is_speaker_line(self, line: str) -> bool:
        """Check if line starts with speaker label"""
        return bool(re.match(r'^Speaker [A-E]:', line.strip()))
    
    def _split_long_block(self, block_lines: List[str], max_chars: int) -> List[str]:
        """Split long speaker blocks at sentence boundaries"""
        if not block_lines:
            return []
        
        # Extract speaker label from first line
        header_match = re.match(r'^(Speaker [A-E]:)', block_lines[0].strip())
        speaker_label = header_match.group(1) if header_match else "Speaker A:"
        
        # Join all content
        content = '\n'.join(block_lines)
        
        # Split by sentences
        sentences = re.split(r'(?<=[.?!])\s+', content)
        
        chunks = []
        current_chunk = speaker_label + " "
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = speaker_label + " " + sentence
            else:
                current_chunk += sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_text_by_speakers(self, text: str) -> List[str]:
        """Split text into chunks respecting speaker boundaries (merging consecutive same-speaker lines)"""
        lines = text.splitlines()
        
        # Ensure first line has speaker label
        if not self._is_speaker_line(lines[0]):
            logger.warning("First line missing speaker label. Assuming 'Speaker A:'")
            lines[0] = f"Speaker A: {lines[0]}"
        
        # First, merge consecutive same-speaker lines (like base code does)
        merged_blocks = []
        current_speaker = None
        current_block_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if self._is_speaker_line(line):
                # Extract speaker from line
                speaker_match = re.match(r'^(Speaker [A-E]):', line.strip())
                if speaker_match:
                    speaker = speaker_match.group(1)
                    line_content = line[len(speaker)+1:].strip()  # Content after "Speaker X:"
                    
                    if current_speaker == speaker:
                        # Same speaker, merge content
                        if line_content:  # Only add non-empty content
                            current_block_lines.append(line_content)
                    else:
                        # Different speaker, save previous block
                        if current_block_lines and current_speaker:
                            merged_text = f"{current_speaker}: {' '.join(current_block_lines)}"
                            merged_blocks.append(merged_text)
                        
                        # Start new block
                        current_speaker = speaker
                        current_block_lines = [line_content] if line_content else []
            else:
                # Non-speaker line, add to current block if we have a speaker
                if current_speaker and line:
                    current_block_lines.append(line)
        
        # Add final block
        if current_block_lines and current_speaker:
            merged_text = f"{current_speaker}: {' '.join(current_block_lines)}"
            merged_blocks.append(merged_text)
        
        # Now chunk the merged blocks (same logic as base code)
        chunks = []
        
        for block in merged_blocks:
            if len(block) > self.chunk_width:
                # Split long block at sentence boundaries
                sub_blocks = self._split_long_block([block], self.chunk_width)
                chunks.extend(sub_blocks)
            else:
                chunks.append(block)
        
        return chunks