import os
import re
import logging
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class ChunkMergingService:
    """
    Mirrors the functionality of merge_chunks.py
    Consolidates all translated chunks into one Japanese script
    """
    
    def __init__(self):
        logger.info("Chunk merging service initialized")
    
    async def merge_translation_chunks(self, chunks_dir: str, output_file: str) -> str:
        """
        Merge all translation chunks into single Japanese transcript
        
        Args:
            chunks_dir: Directory containing translated chunks
            output_file: Path to save merged transcript
            
        Returns:
            str: Path to merged transcript file
        """
        
        try:
            logger.info(f"Starting chunk merging from: {chunks_dir}")
            
            if not os.path.exists(chunks_dir):
                raise ValueError(f"Chunks directory not found: {chunks_dir}")
            
            # Get all chunk files and sort them numerically
            chunk_files = []
            for filename in os.listdir(chunks_dir):
                if filename.startswith('chunk_') and filename.endswith('.txt') and not filename.endswith('_ERROR.txt'):
                    # Extract chunk number for proper sorting
                    match = re.match(r'chunk_(\d+)\.txt', filename)
                    if match:
                        chunk_num = int(match.group(1))
                        chunk_files.append((chunk_num, filename))
            
            if not chunk_files:
                raise ValueError(f"No valid chunk files found in {chunks_dir}")
            
            # Sort by chunk number
            chunk_files.sort(key=lambda x: x[0])
            logger.info(f"Found {len(chunk_files)} chunks to merge")
            
            merged_content = []
            failed_chunks = []
            
            # Read and merge each chunk
            for chunk_num, filename in chunk_files:
                chunk_path = os.path.join(chunks_dir, filename)
                
                try:
                    with open(chunk_path, 'r', encoding='utf-8') as f:
                        chunk_content = f.read().strip()
                    
                    if chunk_content:
                        # Remove any chunk header artifacts that might have been added
                        chunk_content = self._clean_chunk_content(chunk_content)
                        
                        # Add chunk separator comment for debugging (will be cleaned later)
                        merged_content.append(f"=== TRANSLATION CHUNK chunk_{chunk_num:03}.txt ===")
                        merged_content.append(chunk_content)
                        merged_content.append("")  # Blank line between chunks
                        
                        logger.info(f"Merged chunk {chunk_num:03}")
                    else:
                        failed_chunks.append(filename)
                        logger.warning(f"Empty content in chunk {filename}")
                        
                except Exception as e:
                    failed_chunks.append(filename)
                    logger.error(f"Failed to read chunk {filename}: {e}")
            
            if not merged_content:
                raise ValueError("No content was successfully merged from chunks")
            
            # Join all content
            final_content = '\n'.join(merged_content)
            
            # Final cleanup
            final_content = self._final_cleanup(final_content)
            
            # Save merged file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            logger.info(f"Merged transcript saved: {output_file}")
            
            if failed_chunks:
                logger.warning(f"Failed to merge {len(failed_chunks)} chunks: {failed_chunks}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Chunk merging failed: {e}")
            raise Exception(f"Chunk merging failed: {str(e)}")
    
    def _clean_chunk_content(self, content: str) -> str:
        """Clean individual chunk content before merging"""
        
        # Remove any existing chunk markers that might have been included
        content = re.sub(r'=== TRANSLATION CHUNK .*? ===\n?', '', content)
        
        # Remove extra whitespace at start and end
        content = content.strip()
        
        # Normalize line endings
        content = re.sub(r'\r\n', '\n', content)
        
        # Remove excessive blank lines within chunk (but preserve intentional spacing)
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content
    
    def _final_cleanup(self, content: str) -> str:
        """Final cleanup of merged content"""
        
        # Split into lines for processing
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Keep chunk markers for now (will be removed by cleaning service)
            if line.startswith('=== TRANSLATION CHUNK'):
                cleaned_lines.append(line)
                continue
            
            # Clean up speaker lines
            if re.match(r'^Speaker [A-E]:', line):
                # Ensure consistent formatting
                line = re.sub(r'^(Speaker [A-E]):\s*', r'\1: ', line)
                cleaned_lines.append(line)
            elif line.strip():
                # Non-empty line that's not a speaker line
                cleaned_lines.append(line)
            else:
                # Empty line - preserve for spacing
                cleaned_lines.append('')
        
        # Join and do final normalization
        final_content = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive blank lines (but keep some spacing)
        final_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_content)
        
        # Ensure file ends with single newline
        final_content = final_content.rstrip() + '\n'
        
        return final_content
    
    def get_merge_statistics(self, merged_file: str) -> Dict:
        """Get statistics about the merged file"""
        
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Count different elements
            chunk_markers = len(re.findall(r'=== TRANSLATION CHUNK', content))
            speaker_lines = len([line for line in lines if re.match(r'^Speaker [A-E]:', line)])
            total_lines = len([line for line in lines if line.strip()])
            
            # Count speakers
            speakers = set()
            for line in lines:
                match = re.match(r'^(Speaker [A-E]):', line)
                if match:
                    speakers.add(match.group(1))
            
            # Count Japanese characters (rough estimate)
            japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content))
            
            return {
                "total_lines": total_lines,
                "speaker_lines": speaker_lines,
                "chunk_count": chunk_markers,
                "speakers_found": list(speakers),
                "speaker_count": len(speakers),
                "japanese_char_count": japanese_chars,
                "total_char_count": len(content),
                "file_size_kb": round(len(content.encode('utf-8')) / 1024, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get merge statistics: {e}")
            return {"error": str(e)}
    
    def validate_merged_file(self, merged_file: str) -> Dict:
        """Validate that the merged file looks correct"""
        
        try:
            with open(merged_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            warnings = []
            
            # Check for chunk markers (should exist before cleaning)
            chunk_count = len(re.findall(r'=== TRANSLATION CHUNK', content))
            if chunk_count == 0:
                warnings.append("No chunk markers found - file may have been pre-cleaned")
            
            # Check for speaker consistency
            lines = content.split('\n')
            speaker_lines = [line for line in lines if re.match(r'^Speaker [A-E]:', line)]
            
            if len(speaker_lines) == 0:
                issues.append("No speaker lines found")
            
            # Check for Japanese content
            japanese_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', content))
            if japanese_chars == 0:
                issues.append("No Japanese characters found")
            
            # Check file size
            if len(content) < 100:
                issues.append("File appears too short")
            
            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "chunk_count": chunk_count,
                "speaker_line_count": len(speaker_lines),
                "japanese_char_count": japanese_chars
            }
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                "is_valid": False,
                "error": str(e)
            }