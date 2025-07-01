# Audio Translation Service

A standalone FastAPI microservice that converts English audio files to Japanese audio files through a 3-step automated workflow:

1. **Extract English Text**: Speech-to-text using AssemblyAI with speaker diarization
2. **Translate to Japanese**: Text translation using OpenAI API  
3. **Generate Japanese Audio**: Text-to-speech using Google Cloud TTS with multi-speaker support

## Features

- 🎧 **Speaker Diarization**: Maintains separate speaker voices in translation
- 🔄 **Background Processing**: Asynchronous job processing with status tracking
- 📁 **File Management**: Upload, process, and download result files
- 🐳 **Docker Ready**: Complete containerization for easy deployment
- 📊 **Progress Monitoring**: Real-time status updates and progress tracking
- 🛡️ **Error Handling**: Comprehensive error handling and retry mechanisms

## Prerequisites

Before running the service, you need API keys for the following services:

### 1. AssemblyAI API Key
- Sign up at [AssemblyAI](https://www.assemblyai.com)
- Get your API key from the dashboard
- Free tier includes up to 460 hours

### 2. OpenAI API Key  
- Sign up at [OpenAI Platform](https://platform.openai.com)
- Create an API key at [API Keys page](https://platform.openai.com/settings/organization/api-keys)

### 3. Google Cloud Service Account
- Create a project in [Google Cloud Console](https://console.cloud.google.com)
- Enable the [Text-to-Speech API](https://console.cloud.google.com/marketplace/product/google/texttospeech.googleapis.com)
- Create a service account with Editor role
- Download the JSON key file
- **Place the downloaded JSON file in the translation-service directory as `google-credentials.json`**

## Quick Start with Docker
  Steps to Start Docker Desktop:

  1. Open Docker Desktop:

  - Click Spotlight (🔍) or press Cmd + Space
  - Type "Docker" and press Enter
  - Or go to Applications → Docker.app

  2. Wait for Docker to Start:

  - You'll see the Docker whale icon in your menu bar (top right)
  - Wait until the icon becomes solid/static (not animated)
  - It may take 1-2 minutes to fully start

  3. Verify Docker is Running:

  docker --version
  # Should show: Docker version XX.X.X, build...

  4. If previous docker container is running or still exist
   
    docker rm audio-translation-service

    or

    docker rm 2052695ffb41 #(i.e., container id)


  5. Then Try Building:

### 1. Build the Docker Image

```bash
# Navigate to the translation-service directory
cd translation-service

# Build the Docker image
docker build -t audio-translation-service .
```

### 2. Prepare Environment Variables

Copy the example environment file and add your API credentials:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your actual API keys
# ASSEMBLYAI_API_KEY=your_actual_assemblyai_key
# OPENAI_API_KEY=sk-your_actual_openai_key
# GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
```

Or create the `.env` file directly:

```bash
# Create environment file
cat > .env << EOF
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
OPENAI_API_KEY=sk-your_openai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
FASTAPI_ENV=development
LOG_LEVEL=INFO
EOF
```

### 3. Run the Container

```bash
# Run with volume mounts for persistence and credentials
docker run -d \
  --name audio-translation-service \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/google-credentials.json:/app/credentials/google-credentials.json:ro \
  audio-translation-service
```

### 4. Verify Service is Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "service": "audio-translation"}
```

## API Endpoints

The service exposes the following REST API endpoints:

### Health Check
```bash
GET /health
```

### Upload Audio File
```bash
POST /translation/upload
Content-Type: multipart/form-data

Parameters:
- file: Audio file (mp3, wav, m4a, flac)
- user_id: Integer user identifier

Response:
{
  "job_id": "uuid-string",
  "status": "uploaded", 
  "message": "File uploaded successfully. Processing started."
}

example:
input: to Stand alone service
  curl -X POST "http://localhost:8000/translation/upload?user_id=1" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@/Users/sammy.samejima/Downloads/joe-charlie-first-5min.mp3"

input: to web service
  curl -X POST "http://localhost:8001/translation/upload?user_id=1" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@/Users/sammy.samejima/Downloads/joe-charlie-first-5min.mp3"

result:
    {"job_id":"b23d7764-2d8f-4bca-857d-c260325ceefb","status":"uploaded","message":"File uploaded successfully. Processing started."}%  
```

### Check Job Status
```bash
GET /translation/status/{job_id}

example:
input:
 curl "http://localhost:8000/translation/status/b23d7764-2d8f-4bca-857d-c260325ceefb"

Response:
{
  "job_id": "uuid-string",
  "status": "COMPLETED",
  "progress": 100,
  "message": "Translation completed successfully! 🎉",
  "error": null,
  "files": [
    {"type": "english_transcript", "available": true},
    {"type": "japanese_transcript", "available": true}, 
    {"type": "japanese_audio", "available": true}
  ]
}
```

### Download Result Files
```bash
GET /translation/download/{job_id}/{file_type}

example:
  Download the Files:

  1. Japanese Audio (the main output):
    curl -o "japanese_audio.mp3" "http://localhost:8000/translation/download/b23d7764-2d8f-4bca-857d-c260325ceefb/japanese_audio"

  2. Japanese Text:
    curl -o "japanese_transcript.txt" "http://localhost:8000/translation/download/b23d7764-2d8f-4bca-857d-c260325ceefb/japanese_transcript"

  3. English Text:
    curl -o "english_transcript.txt" "http://localhost:8000/translation/download/b23d7764-2d8f-4bca-857d-c260325ceefb/english_transcript"

  Then Check What Downloaded:

file_type options:
- english_transcript: Original English transcript with speaker labels
- japanese_transcript: Japanese translation with speaker labels  
- japanese_audio: Final Japanese audio file (MP3)
```

### Get User Jobs
```bash
GET /translation/jobs/{user_id}

Response:
{
  "jobs": [
    {
      "job_id": "uuid-string",
      "original_filename": "conversation.mp3",
      "status": "COMPLETED",
      "progress": 100,
      "created_at": "2024-01-15T10:30:00",
      "completed_at": "2024-01-15T10:45:00"
    }
  ]
}
```

Alternatively, we can copy the data from docker_volume
docker cp audio-translation-service:/app/outputs/ ./my-outputs/
✅ To use docker cp, you must:
	•	Make sure Docker is running (e.g., Docker Desktop is open and active on Mac).
	•	The container (audio-translation-service) can be running or stopped — that’s okay.

⏺ Docker volumes are NOT automatically cleaned - they persist until you explicitly remove them.

  To see the inside the container
  docker volume ls
    DRIVER    VOLUME NAME
    local     audio-translation-web_mysql_data
    local     audio-translation-web_translation_outputs
    local     audio-translation-web_translation_uploads

  docker run --rm -it \
    -v audio-translation-web_translation_outputs:/data \
    alpine \
    sh

  Volume cleanup scenarios:

  1. Automatic cleanup (when using docker-compose):
  docker-compose down -v  # Removes containers AND volumes
  2. Manual cleanup:
  # Remove specific volume
  docker volume rm audio-translation-web_translation_outputs

  # Remove all unused volumes
  docker volume prune
  3. Check volume usage:
  docker volume ls
  docker system df  # Shows disk usage including volumes

  

## File Management

### Volume Mounts
The service uses two main directories that should be mounted as volumes:

- `/app/uploads`: Stores uploaded audio files
- `/app/outputs`: Stores processed results and intermediate files

### Directory Structure
```
/app/outputs/{job_id}/
├── processed/              # Preprocessed audio chunks
├── transcript_en_raw.txt   # Raw AssemblyAI transcript
├── transcript_en_formatted.txt  # Formatted with speaker labels
├── translation_chunks/     # Individual translation chunks
├── transcript_ja_merged.txt     # Merged Japanese transcript
├── transcript_ja_clean.txt      # Cleaned Japanese text
├── audio_segments/         # Individual TTS audio segments
└── full_audio_jp.mp3      # Final Japanese audio file
```

## Environment Variables

### Configuration Precedence

- **`.env` file ALWAYS wins** when the variable is set
- **Code defaults are fallbacks** - they only apply when no env variable exists  
- **You can run without `.env`** - the service will use safe code defaults
- **Customization is easy** - just add variables to `.env` to override defaults

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ASSEMBLYAI_API_KEY` | Yes | AssemblyAI API key for speech-to-text | `abc123...` |
| `OPENAI_API_KEY` | Yes | OpenAI API key for translation | `sk-...` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to Google Cloud service account JSON | `/app/credentials/google-credentials.json` |

## Example Usage

### 1. Upload an Audio File
```bash
curl -X POST "http://localhost:8000/translation/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@conversation.mp3" \
  -F "user_id=1"
```

### 2. Monitor Progress  
```bash
# Replace {job_id} with actual job ID from upload response
curl "http://localhost:8000/translation/status/{job_id}"
```

### 3. Download Results
```bash
# Download Japanese audio
curl -O "http://localhost:8000/translation/download/{job_id}/japanese_audio"

# Download Japanese transcript  
curl -O "http://localhost:8000/translation/download/{job_id}/japanese_transcript"

# Download English transcript
curl -O "http://localhost:8000/translation/download/{job_id}/english_transcript"
```

## Processing Workflow

The service follows a detailed 3-step workflow:

### Step 1: Extract English Text (20-50% progress)
1. **Audio Preprocessing**: Clean audio and create chunks for better processing
2. **Speech-to-Text**: Use AssemblyAI to transcribe with speaker diarization
3. **Text Formatting**: Format transcript with proper speaker labels

### Step 2: Translate to Japanese (50-85% progress)  
1. **Chunk Translation**: Translate text in manageable chunks using OpenAI
2. **Merge Chunks**: Combine translated chunks into single document
3. **Text Cleaning**: Remove artifacts and clean Japanese text

### Step 3: Generate Japanese Audio (85-100% progress)
1. **Text-to-Speech**: Generate audio using Google Cloud TTS with multiple voices
2. **Audio Merging**: Combine audio segments into final MP3 file

## Testing the Service

### Quick Test with Sample Audio

Here's how to test the translation service with your own audio file:

#### Prerequisites
1. **Start Docker Desktop** and ensure it's running
2. **Update API keys** in `.env` file (replace placeholder values)
3. **Place Google credentials** as `google-credentials.json` in translation-service directory
4. **Prepare test audio file** (MP3, WAV, M4A, or FLAC format)

#### Test Steps

**1. Navigate to translation-service directory:**
```bash
cd /path/to/audio-translation-web/translation-service/
```

**2. Build the Docker image:**
```bash
docker build -t audio-translation-service .
```

**3. Run the container:**
```bash
docker run -d \
  --name audio-translation-service \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/google-credentials.json:/app/credentials/google-credentials.json:ro \
  audio-translation-service
```

**4. Verify service is running:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "service": "audio-translation"}
```

**5. Upload test audio file:**
```bash
curl -X POST "http://localhost:8000/translation/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/audio.mp3" \
  -F "user_id=1"
  
# Example with specific file:
# -F "file=@~/Downloads/joe-charlie-first-5min.mp3" \
```

**6. Monitor translation progress:**
```bash
# Replace {job_id} with actual job ID from upload response
curl "http://localhost:8000/translation/status/{job_id}"

# Check every 30 seconds until status shows "COMPLETED"
```

**7. Download results when complete:**
```bash
# Download Japanese audio
curl -O "http://localhost:8000/translation/download/{job_id}/japanese_audio"

# Download Japanese transcript  
curl -O "http://localhost:8000/translation/download/{job_id}/japanese_transcript"

# Download English transcript
curl -O "http://localhost:8000/translation/download/{job_id}/english_transcript"
```

**8. Check generated files:**
```bash
# View outputs directory
ls -la outputs/{job_id}/

# Listen to Japanese audio
open full_audio_jp.mp3  # On Mac
# Or: vlc full_audio_jp.mp3  # Linux
```

**9. Clean up when done:**
```bash
docker stop audio-translation-service
docker rm audio-translation-service
```

### Expected Processing Time

For a **5-minute audio file**, expect approximately:
- **Step 1** (Audio → English text): 2-3 minutes
- **Step 2** (English → Japanese text): 3-5 minutes  
- **Step 3** (Japanese text → Audio): 5-8 minutes
- **Total**: 10-16 minutes

Processing time varies based on:
- Audio length and quality
- API response times
- Network connectivity
- Chunk size configuration

### Test Tips

- **Monitor logs**: `docker logs audio-translation-service -f`
- **Check file sizes**: Outputs should be in `outputs/{job_id}/` directory
- **Resume capability**: If processing fails, restart container - it will resume from last completed step
- **Rate limits**: Service automatically handles API rate limiting with delays

## Docker Compose (Alternative)

For easier management, you can also use Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'

services:
  translation-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ASSEMBLYAI_API_KEY=${ASSEMBLYAI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY} 
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./google-credentials.json:/app/credentials/google-credentials.json:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

Run with:
```bash
docker-compose up --build
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check container logs
docker logs audio-translation-service

# Check if required API keys are set
docker exec audio-translation-service env | grep -E "(ASSEMBLYAI|OPENAI|GOOGLE)"
```

**Port conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000

# Use different port
docker run -p 8080:8000 audio-translation-service
```

**API key issues:**
```bash
# Verify API keys work
docker exec audio-translation-service python -c "
import os
print('AssemblyAI:', bool(os.getenv('ASSEMBLYAI_API_KEY')))
print('OpenAI:', bool(os.getenv('OPENAI_API_KEY')))
print('Google:', os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')))
"
```

**Storage issues:**
```bash
# Check disk space
df -h

# Clean up old job outputs
docker exec audio-translation-service find /app/outputs -type d -mtime +7 -exec rm -rf {} +
```

### Performance Considerations

- **File Size**: Larger audio files take longer to process (expect 2-5x audio duration)
- **API Limits**: Respect rate limits for AssemblyAI, OpenAI, and Google TTS
- **Storage**: Each job can use 50-200MB depending on audio length
- **Memory**: Service uses ~500MB-1GB RAM during active processing

## Security Notes

- The service runs as a non-root user inside the container
- API keys should be provided via environment variables, not hardcoded
- Google Cloud credentials file should be mounted read-only
- Consider using Docker secrets in production environments

## Integration

This service is designed to integrate with the larger `audio-translation-web` application but can be used standalone. For integration with other applications:

1. **Health Checks**: Use `/health` endpoint for monitoring
2. **Webhook Support**: Consider adding webhook notifications for job completion
3. **Authentication**: Add JWT or API key authentication for production use
4. **Rate Limiting**: Implement rate limiting based on your needs

---

**Built with FastAPI, AssemblyAI, OpenAI, and Google Cloud TTS** 🎵→📝→🎌→🎵