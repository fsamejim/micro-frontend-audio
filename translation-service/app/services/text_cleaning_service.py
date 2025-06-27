import os
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class TextCleaningService:
    """
    Mirrors the functionality of clean_japanese_dialogue.py
    Cleans unnecessary characters from translated Japanese text including chunk markers
    """
    
    def __init__(self):
        # Configure text processing parameters
        self.line_length_threshold = int(os.getenv("TEXT_LINE_LENGTH_THRESHOLD", "500"))
        logger.info("Text cleaning service initialized")
    
    async def clean_japanese_text(self, input_file: str, output_file: str) -> str:
        """
        Clean Japanese translated text by removing chunk markers and formatting artifacts
        
        Args:
            input_file: Path to merged Japanese transcript with chunk markers
            output_file: Path to save cleaned Japanese transcript
            
        Returns:
            str: Path to cleaned transcript file
        """
        
        try:
            logger.info(f"Starting Japanese text cleaning: {input_file}")
            
            # Read the merged file
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Step 1: Remove chunk markers
            content = self._remove_chunk_markers(content)
            
            # Step 2: Clean speaker formatting
            content = self._clean_speaker_formatting(content)
            
            # Step 3: Remove unwanted characters and artifacts
            content = self._remove_artifacts(content)
            
            # Step 4: Normalize spacing and line breaks
            content = self._normalize_spacing(content)
            
            # Step 5: Final Japanese text validation and cleanup
            content = self._final_japanese_cleanup(content)
            
            # Save cleaned file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Cleaned Japanese text saved: {output_file}")
            
            # Log statistics
            stats = self._get_cleaning_stats(content)
            logger.info(f"Cleaning stats: {stats}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Japanese text cleaning failed: {e}")
            raise Exception(f"Text cleaning failed: {str(e)}")
    
    def _remove_chunk_markers(self, content: str) -> str:
        """Remove chunk markers like '=== TRANSLATION CHUNK chunk_xxx.txt ==='"""
        
        # Remove chunk markers with various formats
        patterns = [
            r'=== TRANSLATION CHUNK chunk_\d+\.txt ===\s*\n?',
            r'=== TRANSLATION CHUNK .*? ===\s*\n?',
            r'===.*?CHUNK.*?===\s*\n?',
            r'=== chunk_\d+\.txt ===\s*\n?'
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        return content
    
    def _clean_speaker_formatting(self, content: str) -> str:
        """Ensure consistent speaker formatting"""
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            if re.match(r'^Speaker [A-E]:', line):
                # Ensure consistent spacing after colon
                line = re.sub(r'^(Speaker [A-E]):\s*', r'\1: ', line)
                
                # Remove empty speaker lines
                text_part = line.split(':', 1)[1].strip()
                if text_part:
                    cleaned_lines.append(line)
            elif line:
                # Non-speaker line - keep if not empty
                cleaned_lines.append(line)
            else:
                # Empty line - preserve for spacing
                cleaned_lines.append('')
        
        return '\n'.join(cleaned_lines)
    
    def _remove_artifacts(self, content: str) -> str:
        """Remove various artifacts that might appear in translation"""
        
        # Remove common translation artifacts
        artifacts = [
            r'\[翻訳者注:.*?\]',  # Translator notes
            r'\[注:.*?\]',       # Notes
            r'\(翻訳:.*?\)',     # Translation notes
            r'\*\*.*?\*\*',      # Bold formatting
            r'\_\_.*?\_\_',      # Underscore formatting
            r'\#\#.*?\#\#',      # Hash formatting
            r'```.*?```',        # Code blocks
            r'---+',             # Horizontal lines
            r'===+',             # Equal sign lines
        ]
        
        for pattern in artifacts:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Remove HTML-like tags if any
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove URLs if any
        content = re.sub(r'https?://\S+', '', content)
        
        # Remove email addresses if any
        content = re.sub(r'\S+@\S+\.\S+', '', content)
        
        return content
    
    def _normalize_spacing(self, content: str) -> str:
        """Normalize spacing and line breaks"""
        
        # Split into lines
        lines = content.split('\n')
        normalized_lines = []
        
        prev_was_empty = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                # Empty line
                if not prev_was_empty:
                    normalized_lines.append('')
                prev_was_empty = True
            else:
                # Non-empty line
                normalized_lines.append(line)
                prev_was_empty = False
        
        # Join lines
        content = '\n'.join(normalized_lines)
        
        # Remove triple or more consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Ensure proper spacing between different speakers
        content = self._add_speaker_spacing(content)
        
        return content
    
    def _add_speaker_spacing(self, content: str) -> str:
        """Add appropriate spacing between different speakers"""
        
        lines = content.split('\n')
        spaced_lines = []
        current_speaker = None
        
        for line in lines:
            if not line.strip():
                spaced_lines.append('')
                continue
            
            # Check if this is a speaker line
            speaker_match = re.match(r'^(Speaker [A-E]):', line)
            
            if speaker_match:
                new_speaker = speaker_match.group(1)
                
                # Add double spacing when speaker changes
                if current_speaker and current_speaker != new_speaker:
                    # Remove any existing empty lines at the end
                    while spaced_lines and not spaced_lines[-1].strip():
                        spaced_lines.pop()
                    
                    # Add double spacing
                    spaced_lines.append('')
                    spaced_lines.append('')
                
                current_speaker = new_speaker
            
            spaced_lines.append(line)
        
        return '\n'.join(spaced_lines)
    
    def _final_japanese_cleanup(self, content: str) -> str:
        """Final cleanup specific to Japanese text"""
        
        # Fix common Japanese punctuation issues
        content = re.sub(r'。\s*。', '。', content)  # Double periods
        content = re.sub(r'、\s*、', '、', content)  # Double commas
        
        # Ensure proper spacing around Japanese punctuation
        content = re.sub(r'([。！？])\s+', r'\1 ', content)
        content = re.sub(r'\s+([、。！？])', r'\1', content)
        
        # Remove excessive whitespace within lines
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if line.strip():
                # Clean whitespace within line but preserve structure
                if re.match(r'^Speaker [A-E]:', line):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        speaker_part = parts[0].strip()
                        text_part = parts[1].strip()
                        line = f"{speaker_part}: {text_part}"
                
                # Remove multiple spaces within line
                line = re.sub(r'  +', ' ', line)
                
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Final normalization
        content = content.strip() + '\n'
        
        return content
    
    def _get_cleaning_stats(self, content: str) -> Dict:
        """Get statistics about the cleaned content"""
        
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        speaker_lines = [line for line in lines if re.match(r'^Speaker [A-E]:', line)]
        
        # Count speakers
        speakers = set()
        for line in speaker_lines:
            match = re.match(r'^(Speaker [A-E]):', line)
            if match:
                speakers.add(match.group(1))
        
        # Count Japanese characters
        japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content))
        total_chars = len(content)
        
        return {
            "total_lines": len(lines),
            "content_lines": len(non_empty_lines),
            "speaker_lines": len(speaker_lines),
            "speakers": list(speakers),
            "speaker_count": len(speakers),
            "japanese_chars": japanese_chars,
            "total_chars": total_chars,
            "japanese_ratio": round(japanese_chars / total_chars * 100, 1) if total_chars > 0 else 0
        }
    
    def validate_cleaned_text(self, cleaned_file: str) -> Dict:
        """Validate that the cleaned text is ready for TTS"""
        
        try:
            with open(cleaned_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            warnings = []
            
            # Check for remaining chunk markers
            if '===' in content:
                issues.append("Chunk markers still present")
            
            # Check for speaker lines
            speaker_lines = re.findall(r'^Speaker [A-E]:', content, re.MULTILINE)
            if len(speaker_lines) == 0:
                issues.append("No speaker lines found")
            
            # Check for Japanese content
            japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content))
            if japanese_chars == 0:
                issues.append("No Japanese characters found")
            
            # Check for artifacts
            if re.search(r'[<>{}[\]]', content):
                warnings.append("Possible formatting artifacts remaining")
            
            if re.search(r'https?://', content):
                warnings.append("URLs found in text")
            
            # Check line length (very long lines might cause TTS issues)
            lines = content.split('\n')
            long_lines = [i for i, line in enumerate(lines, 1) if len(line) > self.line_length_threshold]
            if long_lines:
                warnings.append(f"Very long lines found at: {long_lines[:5]}")
            
            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "speaker_line_count": len(speaker_lines),
                "japanese_char_count": japanese_chars,
                "ready_for_tts": len(issues) == 0
            }
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "is_valid": False,
                "error": str(e),
                "ready_for_tts": False
            }