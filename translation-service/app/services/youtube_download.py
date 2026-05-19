import os
import asyncio
import subprocess
import json
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    format_id: Optional[str] = None
    format_note: Optional[str] = None


class YouTubeDownloadService:
    """
    YouTube Download Service
    - Download audio as MP3 for translation input
    - Download video-only as MP4 (Mac-compatible)
    - Auto-detect best Mac-compatible video format
    """

    # Known Mac-compatible format IDs (H.264/AVC1 in MP4 container)
    # Priority order: higher resolution first
    MAC_SAFE_FORMAT_IDS = ["137", "270", "136", "135", "134", "133", "160"]

    def __init__(self):
        self.downloads_dir = "/app/downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)

    async def get_video_info(self, url: str) -> dict:
        """Get video metadata and available formats"""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["yt-dlp", "-J", "--no-warnings", url],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise Exception(f"yt-dlp error: {result.stderr}")

            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            raise Exception("Timeout getting video info")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse video info: {e}")

    async def download_audio(self, url: str, job_id: str) -> DownloadResult:
        """
        Download audio from YouTube as MP3

        Args:
            url: YouTube URL
            job_id: Unique identifier for this download

        Returns:
            DownloadResult with file path on success
        """
        output_dir = os.path.join(self.downloads_dir, job_id)
        os.makedirs(output_dir, exist_ok=True)

        output_template = os.path.join(output_dir, "audio.%(ext)s")
        output_path = os.path.join(output_dir, "audio.mp3")

        try:
            logger.info(f"Downloading audio from: {url}")

            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "yt-dlp",
                    "-x",                          # Extract audio
                    "--audio-format", "mp3",       # Convert to MP3
                    "--audio-quality", "0",        # Best quality
                    "-o", output_template,
                    "--no-warnings",
                    url
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp audio download failed: {result.stderr}")
                return DownloadResult(success=False, error=result.stderr)

            if os.path.exists(output_path):
                logger.info(f"Audio downloaded successfully: {output_path}")
                return DownloadResult(success=True, file_path=output_path)
            else:
                # Check if file exists with different extension
                for ext in ["mp3", "m4a", "wav", "opus", "webm"]:
                    alt_path = os.path.join(output_dir, f"audio.{ext}")
                    if os.path.exists(alt_path):
                        return DownloadResult(success=True, file_path=alt_path)

                return DownloadResult(success=False, error="Audio file not found after download")

        except subprocess.TimeoutExpired:
            return DownloadResult(success=False, error="Download timed out (10 minutes)")
        except Exception as e:
            logger.error(f"Audio download error: {e}")
            return DownloadResult(success=False, error=str(e))

    async def find_mac_compatible_format(self, url: str) -> Optional[dict]:
        """
        Find the best Mac-compatible video format

        Priority:
        1. MP4 container (not webm)
        2. AVC1/H.264 codec (not av01 or vp9)
        3. HTTPS protocol (not m3u8/HLS when possible)
        4. Higher resolution preferred
        """
        try:
            info = await self.get_video_info(url)
            formats = info.get("formats", [])

            # Filter video-only formats
            video_formats = [
                f for f in formats
                if f.get("vcodec", "none") != "none"
                and f.get("acodec", "none") == "none"
            ]

            if not video_formats:
                logger.warning("No video-only formats found")
                return None

            # Score each format for Mac compatibility
            def mac_compatibility_score(fmt: dict) -> tuple:
                score = 0
                format_id = fmt.get("format_id", "")
                ext = fmt.get("ext", "")
                vcodec = fmt.get("vcodec", "").lower()
                protocol = fmt.get("protocol", "")
                height = fmt.get("height", 0) or 0

                # Known good format IDs get highest priority
                if format_id in self.MAC_SAFE_FORMAT_IDS:
                    score += 1000

                # Prefer MP4 container
                if ext == "mp4":
                    score += 100

                # Prefer AVC1/H.264 codec
                if "avc1" in vcodec or "h264" in vcodec:
                    score += 50
                elif "av01" in vcodec or "vp9" in vcodec or "vp09" in vcodec:
                    score -= 50  # Penalize incompatible codecs

                # Prefer HTTPS over HLS
                if protocol == "https":
                    score += 20
                elif "m3u8" in protocol:
                    score -= 10

                return (score, height)

            # Sort by compatibility score, then by resolution
            video_formats.sort(key=mac_compatibility_score, reverse=True)

            best_format = video_formats[0]
            score, _ = mac_compatibility_score(best_format)

            logger.info(f"Best Mac-compatible format: {best_format.get('format_id')} "
                       f"({best_format.get('ext')}, {best_format.get('vcodec')}, "
                       f"{best_format.get('height')}p) - score: {score}")

            return best_format

        except Exception as e:
            logger.error(f"Error finding Mac-compatible format: {e}")
            return None

    async def download_video(self, url: str, job_id: str, format_id: Optional[str] = None) -> DownloadResult:
        """
        Download video-only from YouTube (Mac-compatible MP4)

        Args:
            url: YouTube URL
            job_id: Unique identifier for this download
            format_id: Specific format ID (auto-detect if None)

        Returns:
            DownloadResult with file path on success
        """
        output_dir = os.path.join(self.downloads_dir, job_id)
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "video.mp4")

        try:
            # Auto-detect best format if not specified
            if not format_id:
                best_format = await self.find_mac_compatible_format(url)
                if best_format:
                    format_id = best_format.get("format_id")
                    format_note = f"{best_format.get('ext')} {best_format.get('height')}p {best_format.get('vcodec')}"
                else:
                    # Fallback: let yt-dlp pick best video-only MP4 with H.264
                    # This format string tells yt-dlp to find the best match automatically
                    format_id = "bestvideo[ext=mp4][vcodec^=avc1]/bestvideo[ext=mp4]/bestvideo"
                    format_note = "auto-selected by yt-dlp"
            else:
                format_note = f"user-specified: {format_id}"

            logger.info(f"Downloading video format {format_id} from: {url}")

            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "yt-dlp",
                    "-f", format_id,
                    "-o", output_path,
                    "--no-warnings",
                    url
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp video download failed: {result.stderr}")
                return DownloadResult(success=False, error=result.stderr, format_id=format_id)

            if os.path.exists(output_path):
                logger.info(f"Video downloaded successfully: {output_path}")
                return DownloadResult(
                    success=True,
                    file_path=output_path,
                    format_id=format_id,
                    format_note=format_note
                )
            else:
                # Check for alternative extensions
                for ext in ["mp4", "webm", "mkv"]:
                    alt_path = os.path.join(output_dir, f"video.{ext}")
                    if os.path.exists(alt_path):
                        return DownloadResult(
                            success=True,
                            file_path=alt_path,
                            format_id=format_id,
                            format_note=format_note
                        )

                return DownloadResult(success=False, error="Video file not found after download", format_id=format_id)

        except subprocess.TimeoutExpired:
            return DownloadResult(success=False, error="Download timed out (10 minutes)")
        except Exception as e:
            logger.error(f"Video download error: {e}")
            return DownloadResult(success=False, error=str(e))

    async def download_both(self, url: str, job_id: str) -> dict:
        """
        Download both audio and video from YouTube

        Returns:
            dict with audio_result and video_result
        """
        # Run downloads in parallel
        audio_task = asyncio.create_task(self.download_audio(url, job_id))
        video_task = asyncio.create_task(self.download_video(url, job_id))

        audio_result, video_result = await asyncio.gather(audio_task, video_task)

        return {
            "audio": audio_result,
            "video": video_result
        }

    async def list_formats(self, url: str) -> list:
        """List all available formats for a YouTube URL"""
        try:
            info = await self.get_video_info(url)
            formats = info.get("formats", [])

            return [
                {
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f"{f.get('width', '?')}x{f.get('height', '?')}",
                    "vcodec": f.get("vcodec"),
                    "acodec": f.get("acodec"),
                    "filesize": f.get("filesize"),
                    "protocol": f.get("protocol"),
                }
                for f in formats
            ]
        except Exception as e:
            logger.error(f"Error listing formats: {e}")
            raise
