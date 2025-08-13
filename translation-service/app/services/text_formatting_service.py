import os
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class TextFormattingService:
    """
    Mirrors the functionality of massage_text.py
    Makes transcript human readable with proper speaker tags
    """
    
    def __init__(self):
        logger.info("Text formatting service initialized")
    
    async def format_transcript(self, input_file: str, output_file: str) -> str:
        """
        Format transcript to make it human readable with consistent speaker tags
        
        Args:
            input_file: Path to raw transcript
            output_file: Path to save formatted transcript
            
        Returns:
            str: Path to formatted transcript file
        """
        
        try:
            logger.info(f"Starting text formatting: {input_file}")
            
            # Read the raw transcript
            with open(input_file, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            # Split into lines
            lines = raw_text.strip().split('\n')
            formatted_lines = []
            
            current_speaker = None
            speaker_mapping = {}  # Map original speaker IDs to A, B, C, etc.
            speaker_counter = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract speaker and text using regex
                speaker_match = re.match(r'^(Speaker\s+[A-Z0-9]+):\s*(.*)$', line, re.IGNORECASE)
                
                if speaker_match:
                    original_speaker = speaker_match.group(1).strip()
                    text_content = speaker_match.group(2).strip()
                    
                    # Map speaker to consistent A, B, C format
                    if original_speaker not in speaker_mapping:
                        speaker_letter = chr(ord('A') + speaker_counter)
                        speaker_mapping[original_speaker] = f"Speaker {speaker_letter}"
                        speaker_counter += 1
                    
                    mapped_speaker = speaker_mapping[original_speaker]
                    
                    # Add spacing between different speakers
                    if current_speaker and current_speaker != mapped_speaker:
                        formatted_lines.append("")  # Add blank line between speakers
                    
                    current_speaker = mapped_speaker
                    
                    # Format the line
                    if text_content:
                        formatted_lines.append(f"{mapped_speaker}: {text_content}")
                    
                else:
                    # Handle lines without speaker tags (continuation text)
                    if line and current_speaker:
                        # Assume it's continuation of current speaker
                        formatted_lines.append(f"{current_speaker}: {line}")
                    elif line:
                        # Default to Speaker A if no speaker context
                        if "Speaker A" not in speaker_mapping.values():
                            speaker_mapping["default"] = "Speaker A"
                            current_speaker = "Speaker A"
                            speaker_counter = 1
                        formatted_lines.append(f"Speaker A: {line}")
            
            # Join formatted lines
            formatted_text = '\n'.join(formatted_lines)
            
            # Clean up extra whitespace and normalize
            formatted_text = self._clean_text(formatted_text)
            
            # Save formatted transcript
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            logger.info(f"Formatted transcript saved: {output_file}")
            logger.info(f"Speaker mapping: {speaker_mapping}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Text formatting failed: {e}")
            raise Exception(f"Text formatting failed: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text formatting"""
        
        # Remove multiple consecutive blank lines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Fix double colons and ensure consistent spacing after colons
        text = re.sub(r'(Speaker\s+[A-Z0-9]+):\s*:\s*', r'\1: ', text)  # Fix double colons
        text = re.sub(r'(Speaker\s+[A-Z0-9]+):\s*', r'\1: ', text)      # Ensure single space
        
        # Add paragraph breaks to long speaker lines for better translation
        text = self._add_paragraph_breaks(text)
        
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        # Remove empty lines at start and end
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def _add_paragraph_breaks(self, text: str, max_line_chars: int = 400) -> str:
        """Add paragraph breaks within long speaker lines to improve translation quality"""
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Check if this is a speaker line that's too long
            speaker_match = re.match(r'^(Speaker\s+[A-Z0-9]+):\s*(.*)$', line, re.IGNORECASE)
            
            if speaker_match and len(line) > max_line_chars:
                speaker_label = speaker_match.group(1)
                content = speaker_match.group(2).strip()
                
                if not content:
                    processed_lines.append(line)
                    continue
                
                # Split content at sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', content)
                
                # Rebuild with paragraph breaks, keeping it as one speaker turn
                result_parts = [f"{speaker_label}: "]
                current_paragraph = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    # If adding this sentence would make the paragraph too long, start new paragraph
                    if current_paragraph and len(current_paragraph + " " + sentence) > max_line_chars:
                        result_parts.append(current_paragraph.strip())
                        result_parts.append("")  # Empty line for paragraph break
                        current_paragraph = sentence
                    else:
                        if current_paragraph:
                            current_paragraph += " " + sentence
                        else:
                            current_paragraph = sentence
                
                # Add the final paragraph
                if current_paragraph.strip():
                    result_parts.append(current_paragraph.strip())
                
                # Join the speaker label with the first paragraph, then add remaining parts
                if len(result_parts) > 1:
                    first_line = result_parts[0] + result_parts[1] if len(result_parts) > 1 else result_parts[0]
                    processed_lines.append(first_line)
                    processed_lines.extend(result_parts[2:])  # Add remaining paragraphs and breaks
                else:
                    processed_lines.append(line)  # Fallback to original line
                    
            else:
                # Line is fine as-is
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def get_speaker_stats(self, formatted_file: str) -> Dict:
        """Get statistics about speakers in formatted transcript"""
        
        try:
            with open(formatted_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            speaker_stats = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract speaker
                speaker_match = re.match(r'^(Speaker [A-Z]):', line)
                if speaker_match:
                    speaker = speaker_match.group(1)
                    if speaker not in speaker_stats:
                        speaker_stats[speaker] = {
                            'line_count': 0,
                            'word_count': 0,
                            'char_count': 0
                        }
                    
                    # Count stats
                    text_content = line[len(speaker) + 1:].strip()
                    speaker_stats[speaker]['line_count'] += 1
                    speaker_stats[speaker]['word_count'] += len(text_content.split())
                    speaker_stats[speaker]['char_count'] += len(text_content)
            
            return {
                'total_speakers': len(speaker_stats),
                'speaker_details': speaker_stats,
                'total_lines': sum(stats['line_count'] for stats in speaker_stats.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get speaker stats: {e}")
            return {}
    
    async def validate_formatting(self, formatted_file: str) -> Dict:
        """Validate that the formatting is correct"""
        
        try:
            with open(formatted_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            issues = []
            speaker_lines = 0
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with proper speaker format
                if re.match(r'^Speaker [A-Z]:', line):
                    speaker_lines += 1
                    # Check if there's content after the speaker tag
                    if len(line.split(':', 1)) < 2 or not line.split(':', 1)[1].strip():
                        issues.append(f"Line {i}: Empty content after speaker tag")
                else:
                    issues.append(f"Line {i}: Line doesn't start with proper speaker format")
            
            return {
                'is_valid': len(issues) == 0,
                'total_lines': len([l for l in lines if l.strip()]),
                'speaker_lines': speaker_lines,
                'issues': issues[:10]  # Limit to first 10 issues
            }
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'is_valid': False,
                'error': str(e)
            }