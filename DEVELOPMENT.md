# DEVELOPMENT.md

Development notes, feature tracking, and technical decisions for the micro-frontend-audio application.

## Application Overview

A full-stack web application for **audio translation** between Japanese and English, built with:
- **Module Federation** micro-frontend architecture
- **7 containerized services** via Docker Compose
- **Translation pipeline** using AssemblyAI, OpenAI, and Google Cloud TTS

## Architecture

### Service Topology

| Service | Port | Technology | Purpose |
|---------|------|------------|---------|
| shell-app | 3000 | Vite + React | Host MF - Application shell |
| auth-mf | 3001 | Vite + React | Remote MF - Authentication |
| audio-mf | 3002 | Vite + React | Remote MF - Audio processing UI |
| dashboard-mf | 3003 | Vite + React | Remote MF - Analytics |
| backend | 8080 | Spring Boot | JWT auth, user management |
| translation-service | 8001 | FastAPI | Audio translation pipeline |
| database | 3307 | MySQL 8.0 | Persistent storage |

### Translation Pipeline

**Audio Input Flow:**
```
Audio → Preprocessing → Transcription (AssemblyAI) → Formatting → Translation (OpenAI) → Merging → Cleaning → TTS (Google Cloud)
```

**Text Input Flow (faster):**
```
Text → Formatting → Translation (OpenAI) → Merging → Cleaning → TTS (Google Cloud)
```

## Feature Tracking

### Implemented Features

#### Text Input Mode
**Status:** Completed
**Description:** Allows text-to-translated-audio without audio upload

**Changes Made:**
- `audio-mf/src/components/AudioUpload.tsx` - Added toggle between Audio/Text modes
- `audio-mf/src/services/translationService.ts` - Added `textToFile()` helper
- `audio-mf/src/types/translation.ts` - Added `input_type` to response interfaces
- `translation-service/app/main.py` - Backend support for `.txt` file processing

**Configuration:**
```bash
# In translation-service/.env
TEXT_INPUT_MAX_CHARS=50000  # Limit for textarea input
# .txt file uploads have no character limit
```

**Pipeline behavior:**
- Text input skips audio preprocessing and transcription steps
- Retains full regeneration and retry capabilities

---

#### YouTube Download Integration
**Status:** Completed (Hidden Feature)
**Description:** Download YouTube audio (mp3) and video-only (mp4) from URL

**Access:** Hidden route at `http://localhost:3000/youtube` (requires login, not in navigation)

**Files Created/Modified:**
- `translation-service/app/services/youtube_download.py` - Core download logic
- `translation-service/app/main.py` - YouTube endpoints + auto-cleanup
- `translation-service/requirements.txt` - Added yt-dlp dependency (auto-updates)
- `docker-compose.yml` - Added translation_downloads volume
- `audio-mf/src/components/YouTubeDownload.tsx` - Hidden UI component
- `audio-mf/vite.config.ts` - Exposed YouTubeDownload module
- `shell-app/src/App.tsx` - Added hidden /youtube route

**UI Features:**
- URL input field with validation
- Checkboxes for Audio (MP3) and/or Video-only (MP4)
- Download buttons after completion
- Error display for failed downloads

**Auto-Cleanup:**
- Files are automatically deleted from Docker **5 minutes after user downloads**
- Independent timers for audio and video files
- Directory removed when empty

**API Endpoints:**
```bash
# Download audio/video
POST /youtube/download
Body: {"url": "https://youtube.com/...", "type": "audio|video|both"}

# List available formats
GET /youtube/formats?url=https://youtube.com/...

# Download completed file (triggers 5-min cleanup timer)
GET /youtube/download/{job_id}/audio
GET /youtube/download/{job_id}/video
```

**Mac Compatibility Algorithm:**
```python
# Video format selection priority:
# 1. bestvideo[ext=mp4][vcodec^=avc1]  (best MP4 with H.264)
# 2. bestvideo[ext=mp4]                (any MP4)
# 3. bestvideo                         (any video format)
```

**Storage:**
- Temporary storage in Docker volume: `translation_downloads` → `/app/downloads`
- Files auto-deleted 5 minutes after user downloads them

---

### Planned Enhancements

#### YouTube HLS Transcoding (Future)
If only HLS streams are available and Mac playback fails, auto-transcode:
```bash
ffmpeg -i input.mp4 \
  -map 0:v:0 \
  -c:v libx264 \
  -profile:v baseline \
  -level 3.0 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -an \
  output_mac_safe.mp4
```

---

## Docker Storage Notes

### Volume Configuration

Three named volumes store data:

```yaml
volumes:
  translation_uploads:   # Uploaded audio/text files
  translation_outputs:   # Generated outputs (transcripts, audio)
  translation_downloads: # YouTube downloads (auto-cleaned after 5 min)
```

### Current Usage (as of 2026-03)
- `translation_uploads`: ~314MB
- `translation_outputs`: ~1.5GB
- **Total**: ~1.8GB

### Storage Management

```bash
# Check volume sizes
docker system df -v

# List volume contents
docker-compose exec translation-service ls -la /app/uploads
docker-compose exec translation-service ls -la /app/outputs

# Remove old job outputs (careful - data loss)
docker-compose exec translation-service rm -rf /app/outputs/<job_id>
```

### Growth Considerations

**Per-job storage estimates:**
- Audio input: ~50-100MB per hour of audio
- Text input: ~10-50MB (no source audio)
- Each regeneration adds ~10-30MB

**YouTube downloads (auto-cleaned):**
- Audio (mp3): ~10MB per 10 minutes
- Video-only (1080p mp4): ~50-100MB per 10 minutes
- Files deleted 5 minutes after user downloads them

---

## Development Modes

### Recommended: Hybrid Development
```bash
npm run dev:local
```
- Remote MFs in production mode (avoids CORS issues)
- Shell app in development mode (shows React warnings)

### Full Production Testing
```bash
npm run prod:local
```
- All MFs optimized and minified
- Production-ready performance

### Key Finding
HTML validation warnings are React development features, not backend-related. Running all MFs in development mode causes Module Federation CORS issues.

---

## Retry System

The translation service supports smart retry from any failure point:

| Failure Point | Resume From |
|--------------|-------------|
| Audio Preprocessing | Transcription |
| Transcription | Text Formatting |
| Text Formatting | Translation |
| Translation | Chunk Merging |
| Chunk Merging | Text Cleaning |
| Text Cleaning | Audio Generation |
| Audio Generation | Retries audio only |

All intermediate files are preserved and reused on retry.

---

## API Quick Reference

### Translation Service (Port 8001)

```bash
# Upload audio/text
POST /translation/upload?user_id=1&source_language=en&target_language=ja

# Check job status
GET /translation/status/{job_id}

# Get user's jobs
GET /translation/jobs/{user_id}

# Retry failed job
POST /translation/retry/{job_id}

# Download results
GET /translation/download/{job_id}/{file_type}
# file_type: source_transcript, target_transcript, target_audio, target_audio_v1, etc.

# Get available TTS voices
GET /translation/voices?language_code=ja

# Get detected speakers
GET /translation/speakers/{job_id}

# Regenerate audio with custom voices
POST /translation/regenerate-audio/{job_id}
```

### Backend (Port 8080)

```bash
# Authentication
POST /api/auth/login
POST /api/auth/register
GET /api/auth/me

# Health check
GET /actuator/health
```

---

## Troubleshooting

### Common Issues

**DNS resolution failure during job processing:**
- Usually transient Docker networking issue
- Fix: Retry the job

**Module Federation CORS errors:**
- Ensure all remote MFs are built in production mode
- Use `npm run dev:local` (hybrid mode)

**Job stuck at specific step:**
- Check translation-service logs: `docker-compose logs -f translation-service`
- Common causes: API rate limits, network issues
- Solution: Wait and retry

### Useful Commands

```bash
# Full rebuild
docker-compose down && docker-compose up --build

# Rebuild single service
docker-compose build --no-cache audio-mf && docker-compose up -d

# View all service health
for p in 3000 3001 3002 3003 8080 8001; do curl -s http://localhost:$p/health && echo " - Port $p OK"; done
```

---

## Notes

### External API Dependencies

| API | Purpose | Rate Limits |
|-----|---------|-------------|
| AssemblyAI | Speech-to-text | Free tier: 460 hours |
| OpenAI | Translation | Varies by plan |
| Google Cloud TTS | Text-to-speech | 100-1000+ req/min |

### Configuration Files

- `translation-service/.env` - API keys and processing settings
- `docker-compose.yml` - Service orchestration
- `*/vite.config.ts` - Module Federation config
- `*/nginx.conf` - CORS and routing
