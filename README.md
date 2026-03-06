# Micro-Frontend-Audio Application

A modern full-stack web application built with **Module Federation** micro-frontend architecture, featuring independent microfrontends, Spring Boot backend, and containerized deployment. This application demonstrates enterprise-level micro-frontend patterns with seamless module sharing and independent deployability.

## 🏗️ Architecture Overview

This application implements a **Module Federation** architecture with the following services:

- **Shell App** (Host) - Main application shell that orchestrates all microfrontends
- **Auth MF** (Remote) - Authentication microfrontend 
- **Audio MF** (Remote) - Audio processing microfrontend
- **Dashboard MF** (Remote) - Dashboard and analytics microfrontend
- **Backend** - Spring Boot API with JWT authentication
- **Translation Service** - Python FastAPI service for audio translation
- **Database** - MySQL database for persistent storage

## ✨ Features

- 🔗 **Module Federation** - Independent microfrontends with shared dependencies
- 🔐 **JWT Authentication** - Secure authentication across all microfrontends
- 🎵 **Audio Processing** - Complete audio translation pipeline
- 📝 **Text Input Mode** - Translate text directly without audio (see [Text Input Feature](#-text-input-feature))
- 📊 **Real-time Dashboard** - Analytics and monitoring interface
- 🐳 **Full Containerization** - Docker-based deployment with health checks
- 🚀 **Independent Deployment** - Each microfrontend can be deployed separately
- 🛡️ **CORS Security** - Proper cross-origin configuration for Module Federation
- 📱 **Responsive Design** - Modern React UI across all microfrontends

## 🗂️ Project Structure

```
micro-frontend-audio/
├── docker-compose.yml              # Docker orchestration
├── package.json                    # Workspace root configuration
│
├── shell-app/                      # Shell App (Host MF) - Port 3000
│   ├── Dockerfile                  # Shell app container
│   ├── nginx.conf                  # Production nginx config
│   ├── vite.config.ts             # Vite + Module Federation config
│   ├── src/
│   │   ├── components/            # Shell-specific components
│   │   ├── App.tsx               # Main app with MF integration
│   │   └── main.tsx              # Application entry point
│   └── package.json              # Shell dependencies
│
├── auth-mf/                        # Auth Microfrontend - Port 3001  
│   ├── Dockerfile                  # Auth MF container
│   ├── nginx.conf                 # CORS-enabled nginx config
│   ├── vite.config.ts             # Module Federation expose config
│   ├── src/
│   │   ├── components/            # Authentication components
│   │   │   ├── Login.tsx         # Login component
│   │   │   ├── Register.tsx      # Registration component
│   │   │   └── ProtectedRoute.tsx # Route protection
│   │   ├── contexts/              # Auth context
│   │   ├── services/              # Auth API services
│   │   └── App.tsx               # Auth MF entry point
│   └── package.json              # Auth MF dependencies
│
├── audio-mf/                       # Audio Microfrontend - Port 3002
│   ├── Dockerfile                  # Audio MF container
│   ├── nginx.conf                 # CORS-enabled nginx config  
│   ├── vite.config.ts             # Module Federation expose config
│   ├── src/
│   │   ├── components/            # Audio processing components
│   │   ├── services/              # Audio API services
│   │   └── App.tsx               # Audio MF entry point
│   └── package.json              # Audio MF dependencies
│
├── dashboard-mf/                   # Dashboard Microfrontend - Port 3003
│   ├── Dockerfile                  # Dashboard MF container
│   ├── nginx.conf                 # CORS-enabled nginx config
│   ├── vite.config.ts             # Module Federation expose config
│   ├── src/
│   │   ├── components/            # Dashboard components
│   │   ├── services/              # Dashboard API services  
│   │   └── App.tsx               # Dashboard MF entry point
│   └── package.json              # Dashboard MF dependencies
│
├── backend/                        # Spring Boot Backend - Port 8080
│   ├── Dockerfile                  # Backend container
│   ├── src/
│   │   ├── main/java/com/example/frontbackweb/
│   │   │   ├── config/           # Configuration classes
│   │   │   ├── controller/       # REST controllers
│   │   │   ├── model/            # Data models
│   │   │   ├── repository/       # Data access layer
│   │   │   ├── security/         # JWT security implementation
│   │   │   └── service/          # Business logic
│   │   └── resources/
│   │       ├── application.properties
│   │       ├── application-docker.properties  
│   │       └── init.sql          # Database initialization
│   ├── build.gradle              # Backend dependencies
│   └── gradlew                   # Gradle wrapper
│
├── translation-service/            # Python FastAPI Service - Port 8001
│   ├── Dockerfile                  # Translation service container
│   ├── app/
│   │   ├── main.py               # FastAPI application
│   │   ├── models/               # Translation models
│   │   └── services/             # Translation pipeline
│   ├── requirements.txt          # Python dependencies
│   └── README.md                 # Service-specific documentation
│
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** - Required for containerized deployment
- **Node.js 22.x** - For frontend microfrontends
- **Java 21+** - For backend development (optional)

### First Time Setup (Recommended)

For initial installation on a new machine, use the setup script:

```bash
./setup.sh
```

The `./setup.sh` script will:
1. Check prerequisites (Docker, Node.js, npm)
2. Verify port availability
3. Set up environment configuration (`.env` file)
4. Check Google Cloud credentials
5. Install frontend dependencies and build microfrontends (for local dev mode)
6. Optionally start the application (`docker-compose up --build`)

Once setup completes and you choose to start, the application will be running at http://localhost:3000

**Note:** Docker builds the frontend inside containers, so steps 5 is optional but enables local development mode (`npm run dev:local`) if needed later.

### Option 1: Docker (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - **Shell App**: http://localhost:3000 (Main application)
   - **Auth MF**: http://localhost:3001 (Authentication)
   - **Audio MF**: http://localhost:3002 (Audio processing)
   - **Dashboard MF**: http://localhost:3003 (Dashboard)
   - **Backend API**: http://localhost:8080/api
   - **Translation Service**: http://localhost:8001
   - **Database**: localhost:3307 (MySQL)

3. **Default credentials:**
   - Username: `admin`
   - Password: `admin123`

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

For development without Docker:

1. **Install dependencies:**
   ```bash
   npm run install:all
   ```

2. **Start services:**
   ```bash
   # Option A: Hybrid mode (recommended for development)
   npm run dev:local
   
   # Option B: Full production mode (for testing)
   npm run prod:local
   ```

3. **Individual microfrontend commands:**
   ```bash
   npm run build:shell     # Build shell-app
   npm run build:auth      # Build auth-mf
   npm run build:audio     # Build audio-mf
   npm run build:dashboard # Build dashboard-mf
   npm run build:all       # Build all microfrontends
   ```

### Rebuilding After Code Changes

```bash
# Rebuild and restart all services
docker-compose up --build

# If changes aren't being picked up (Docker cache issue), force rebuild:
docker-compose build --no-cache audio-mf && docker-compose up -d

# Or rebuild everything without cache:
docker-compose build --no-cache && docker-compose up
```

**Alternative: Local development mode (faster iteration):**
```bash
# Run frontend locally instead of in Docker (faster for frequent changes)
npm run build:audio && npm run prod:local
```

## 🐳 Docker Deployment

### Services Overview
The Docker stack includes 6 containerized services:

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| **shell-app** | 3000 | Host MF - Main application shell | `/health` |
| **auth-mf** | 3001 | Remote MF - Authentication | `/health` |  
| **audio-mf** | 3002 | Remote MF - Audio processing | `/health` |
| **dashboard-mf** | 3003 | Remote MF - Dashboard | `/health` |
| **backend** | 8080 | Spring Boot API | `/actuator/health` |
| **translation-service** | 8001 | Python FastAPI service | `/health` |
| **database** | 3307 | MySQL 8.0 database | Built-in |

### Docker Commands

```bash
# Start all services (builds images if needed)
docker-compose up --build

# Start in background
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f shell-app
docker-compose logs -f auth-mf
docker-compose logs -f backend

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database data)


# Rebuild specific service
docker-compose build auth-mf
docker-compose up auth-mf

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec database mysql -u sammy -p audiotranslationdb
```
### Example to extract audio from YouTube video ###
brew install yt-dlp
yt-dlp -x --audio-format mp3 --audio-quality 0 "https://www.youtube.com/watch?v=7oAlD3lMNXo"
### Example to download a YouTube video only (no audio) ###
# Find out the available format
yt-dlp -F "https://www.youtube.com/watch?v=BYXbuik3dgA"
# Download video only: ex: 270   mp4   1920x1080 
yt-dlp -f 312 "https://www.youtube.com/watch?v=7oAlD3lMNXo"
yt-dlp -f 270 "https://www.youtube.com/watch?v=BYXbuik3dgA" -o "video.mp4"
# video only - nuclear option
yt-dlp \
-f 270 \
--hls-use-mpegts \
--recode-video mp4 \
-o elon_reencoded.mp4 \
"https://www.youtube.com/watch?v=5eFbeEMFna4"

# Then ✅ Guaranteed fix: Make a “Mac-safe” MP4 (baseline H.264)
ffmpeg -i elon_reencoded.mp4 \
-map 0:v:0 \
-c:v libx264 \
-profile:v baseline \
-level 3.0 \
-pix_fmt yuv420p \
-movflags +faststart \
-an \
elon_qt_safe.mp4


  If your job is completed, you can access the files directly via these URLs (replace {job_id} with your actual Job ID):

  http://localhost:8001/translation/download/{job_id}/japanese_audio
  http://localhost:8001/translation/download/{job_id}/english_transcript
  http://localhost:8001/translation/download/{job_id}/japanese_transcript

    If You're Inside Docker

  The actual output files are stored at:
  /app/outputs/{job_id}/full_audio_jp.mp3          # Final Japanese audio
  /app/outputs/{job_id}/transcript_en_formatted.txt # English transcript
  /app/outputs/{job_id}/transcript_ja_clean.txt     # Japanese transcript
  
### Clean Rebuild Process

```bash
# Complete clean rebuild (recommended for troubleshooting)
docker-compose down
rm -rf */node_modules node_modules
docker system prune -af --volumes
docker-compose up --build
```

## 🔧 Module Federation Configuration

### Development Modes

This project supports two optimized development modes:

**1. Hybrid Development Mode (Recommended):**
```bash
npm run dev:local
```
- **Remote MFs**: Production mode (`vite preview`) - Avoids CORS issues
- **Shell App**: Development mode (`vite dev`) - Shows React warnings  
- **Use case**: Day-to-day development with debugging capabilities

**2. Full Production Mode (Testing):**
```bash
npm run prod:local
```
- **All MFs**: Production mode (`vite preview`) - Fully optimized
- **Performance**: Maximum optimization, no debug warnings
- **Use case**: Production-ready local testing

### Module Federation Architecture

Each microfrontend is independently deployable:

- **Shell App** - Consumes remote modules from other MFs
- **Remote MFs** - Expose specific components via `remoteEntry.js`
- **Shared Dependencies** - React, React-DOM shared across all MFs
- **Independent Builds** - Each MF can be built and deployed separately

## 🔐 Authentication Flow

1. **User Registration/Login** - Handled by Auth MF
2. **JWT Token Generation** - Backend issues JWT tokens
3. **Token Sharing** - Authentication state shared across all MFs
4. **Protected Routes** - Each MF can protect its own routes
5. **Cross-MF Authentication** - Seamless auth state across modules

## 📝 Text Input Feature

The application supports two input modes for translation:

### Input Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Audio File** | Upload MP3, WAV, M4A, FLAC files | Translate podcasts, interviews, lectures |
| **Text** | Paste text directly or upload .txt files | Translate articles, documents, scripts |

### How Text Input Works

When you select **Text** mode:

1. **Paste or Type** - Enter text directly in the textarea (up to 50,000 characters)
2. **Select Direction** - Choose English → Japanese or Japanese → English
3. **Start Translation** - Text is processed through a streamlined pipeline:

```
Text Input → Translation (OpenAI) → Text Cleaning → Audio Generation (Google TTS)
```

**Note:** Text input skips the audio preprocessing and transcription steps, making it faster than audio input.

### Input Limits

| Input Method | Character Limit | Notes |
|--------------|-----------------|-------|
| **Textarea (paste)** | 50,000 chars | ~8,000 words, configurable via `TEXT_INPUT_MAX_CHARS` |
| **.txt file upload** | No limit | Use Audio mode's drag-drop to upload large .txt files |

### Speaker Labels (Optional)

For multi-speaker text, you can include speaker labels:

```
Speaker A: Hello, how are you today?
Speaker B: I'm doing great, thanks for asking!
Speaker A: That's wonderful to hear.
```

If no speaker labels are provided, the entire text is treated as **Speaker A**.

### Configuration

The text input character limit is configurable in `translation-service/.env`:

```bash
# Maximum characters for text input textarea (default: 50000)
TEXT_INPUT_MAX_CHARS=50000
```

### Features Available for Text Input

All standard features work with text input:
- **Job Status Tracking** - Real-time progress updates
- **Job History** - View past text translation jobs
- **Audio Regeneration** - Re-generate audio with different voices
- **Retry on Failure** - Smart resume from last successful step
- **Download Results** - Download translated text and generated audio

## 🌐 API Endpoints

### Backend API (Port 8080)
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user (requires JWT)
- `GET /actuator/health` - Backend health check

### Translation Service API (Port 8001)
- `POST /translate` - Audio translation endpoint
- `GET /health` - Service health check

### Microfrontend Health Checks
- `GET http://localhost:3000/health` - Shell app
- `GET http://localhost:3001/health` - Auth MF
- `GET http://localhost:3002/health` - Audio MF  
- `GET http://localhost:3003/health` - Dashboard MF

## 🧪 Testing Retry Logic (Test Mode)

The translation service includes comprehensive retry functionality with a built-in test mode for simulating failures at specific workflow steps.

⚠️ **Important**: Test mode allows you to artificially simulate failures on **completed jobs** to test the retry functionality. Failures are injected AFTER a job completes successfully, not during processing.

### How Test Mode Works

**When `TEST_MODE=true` (development/testing):**
- ✅ Test endpoints are **available** 
- ✅ You can simulate failures using curl commands
- ✅ Jobs can be artificially marked as failed for retry testing

**When `TEST_MODE=false` (production):**
- ❌ Test endpoints return **404 errors**
- ❌ Curl commands are **blocked** for security
- ❌ No failure simulation possible

### Enabling Test Mode

Test mode is controlled by the `TEST_MODE` environment variable in `/translation-service/.env`:

```bash
# Enable test endpoints for retry testing (development)
TEST_MODE=true

# Disable test endpoints for production security
TEST_MODE=false
```

**To switch test mode without rebuilding:**
```bash
# 1. Edit /translation-service/.env and change TEST_MODE value
# 2. Restart only the translation service
docker-compose restart translation-service

# 3. Verify test mode is active
curl -X POST "http://localhost:8001/translation/test/fail/any-job-id?failure_step=translation"
# Should return error if TEST_MODE=false, success message if TEST_MODE=true
```

### Complete Test Workflow

#### Step 1: Upload and Complete a Job
1. **Upload audio file**: Go to http://localhost:3000 and upload any audio file
2. **Wait for completion**: Let the job complete normally (it should show "Completed" status)
3. **Copy Job ID**: From the Job History page, copy the Job ID (e.g., `f210b6eb-61d2-4662-a676-bc83918168fe`)

#### Step 2: Simulate Failure with Curl Commands

**Example Job ID: `f210b6eb-61d2-4662-a676-bc83918168fe`** (replace with your actual Job ID)

```bash
# Test preprocessing failure (10% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=preprocessing"

# Test transcription failure (30% progress)  
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=transcription"

# Test text formatting failure (50% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=formatting"

# Test translation failure (65% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=translation"

# Test chunk merging failure (78% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=merging"

# Test text cleaning failure (83% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=cleaning"

# Test audio generation failure (95% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=audio_generation"

# Test generic failure (50% progress)
curl -X POST "http://localhost:8001/translation/test/fail/f210b6eb-61d2-4662-a676-bc83918168fe?failure_step=generic"
```

**Expected curl response when TEST_MODE=true:**
```json
{
  "job_id": "f210b6eb-61d2-4662-a676-bc83918168fe",
  "status": "FAILED_TRANSLATION",
  "message": "✅ Test failure injected at 'translation' step. Progress set to 65%. You can now test the retry functionality!",
  "progress": 65,
  "test_mode": true
}
```

**Expected curl response when TEST_MODE=false:**
```json
{
  "detail": "Test endpoints not available (TEST_MODE=false)"
}
```

#### Step 3: Test the Retry Functionality
After running a successful curl command:

1. **Refresh Job History**: Go to http://localhost:3000 and refresh the Job History page
2. **Observe Failure Status**: The job will now show specific failure status:
   - `Failed: Audio Preprocessing` (for preprocessing failure)
   - `Failed: Transcription` (for transcription failure)
   - `Failed: Translation` (for translation failure)
   - `Failed: Audio Generation` (for audio_generation failure)
   - etc.
3. **Click Retry Button**: You'll see a **"Retry from [Step Name]"** button
4. **Monitor Progress**: Click retry and watch the job resume from the exact failure point
5. **Verify Completion**: The job should complete successfully, reusing all previous work

#### Step 4: Repeat Testing
- You can simulate different failure scenarios on the same job
- Each curl command overwrites the previous simulated failure
- Test all 8 failure scenarios to verify comprehensive retry coverage

### Available Failure Scenarios

| Failure Step | Status | Progress | Retry Resumes From | Tests |
|-------------|--------|----------|-------------------|--------|
| `preprocessing` | `FAILED_PREPROCESSING_AUDIO_EN` | 10% | Audio preprocessing | File processing errors |
| `transcription` | `FAILED_TRANSCRIBING_EN` | 30% | Transcription step | AssemblyAI API failures |
| `formatting` | `FAILED_FORMATTING_TEXT_EN` | 50% | Text formatting | Text processing errors |
| `translation` | `FAILED_TRANSLATING_CHUNKS_JP` | 65% | Translation step | OpenAI API failures |
| `merging` | `FAILED_MERGING_CHUNKS_JP` | 78% | Chunk merging | File merging errors |
| `cleaning` | `FAILED_CLEANING_TEXT_JP` | 83% | Text cleaning | Text cleaning errors |
| `audio_generation` | `FAILED_GENERATING_AUDIO_JP` | 95% | Audio generation | Google TTS API failures |
| `generic` | `FAILED` | 50% | Auto-detection | Legacy failure handling |

### Retry Logic Features

- **🎯 Smart Resume**: Detects exact failure point and continues from there
- **💾 File Reuse**: Preserves all intermediate results (transcripts, translations, audio chunks)
- **🔄 Step-by-Step Recovery**: Can resume from any workflow step
- **📊 Progress Preservation**: Maintains realistic progress indicators
- **🛡️ Error Handling**: Comprehensive error messages and status tracking

### Production Deployment

**Important**: Always disable test mode in production:

```bash
# In translation-service/.env
TEST_MODE=false

# Restart the service
docker-compose restart translation-service
```

When `TEST_MODE=false`, test endpoints return 404 errors and are not accessible.

## 🛠️ Technology Stack

### Frontend (All Microfrontends)
- **React 18.3.1** - UI library (stable version)
- **TypeScript** - Type safety
- **Vite 5.4.10** - Build tool (stable version)
- **Module Federation** - Micro-frontend architecture
- **@originjs/vite-plugin-federation** - Module Federation plugin

### Backend & Services
- **Spring Boot 3.2** - Java backend framework
- **Spring Security + JWT** - Authentication & authorization
- **MySQL 8.0** - Database
- **FastAPI** - Python translation service

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **nginx** - Production web server with CORS support
- **Node.js 22.x** - Runtime environment

## 🔍 Troubleshooting

### Module Federation Issues

**CORS Errors:**
```bash
# Check nginx CORS configuration
docker-compose logs auth-mf
docker-compose logs audio-mf

# Verify remoteEntry.js is accessible
curl http://localhost:3001/assets/remoteEntry.js
curl http://localhost:3002/assets/remoteEntry.js
```

**Remote Module Loading Failures:**
```bash
# Check all MF health endpoints
curl http://localhost:3000/health  # Shell
curl http://localhost:3001/health  # Auth
curl http://localhost:3002/health  # Audio  
curl http://localhost:3003/health  # Dashboard
```

**Version Compatibility Issues:**
- Ensure all MFs use the same React version (18.3.1)
- Verify Vite version compatibility (5.4.10)
- Check Module Federation plugin version (1.4.1)

### Docker Issues

**Port Conflicts:**
```bash
# Check what's using the ports
lsof -i :3000 :3001 :3002 :3003 :8080 :8001 :3307

# Kill conflicting processes
sudo kill -9 <PID>
```

**Build Failures:**
```bash
  💡 Safe Commands:

# Safe restart (keeps all data)
# but this will lose the job ID
docker-compose restart

# Safe stop (keeps all data)  
# but this will lose the job ID
docker-compose down
  
# Check volume sizes
docker system df -v

# Completely delete all data
docker-compose down -v
  
# Clean rebuild everything
docker-compose down
docker system prune -af --volumes
rm -rf */node_modules node_modules
docker-compose up --build
```

**Service Health Issues:**
```bash
# Check service status
docker-compose ps

# View specific service logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up database

# Connect to database directly
docker-compose exec database mysql -u sammy -ppassword123 audiotranslationdb

# Check database health
docker-compose exec database mysqladmin -u sammy -ppassword123 ping -h localhost
```

## 🚦 Development Workflow

### Getting Started
1. **Clone the repository**
2. **Start with Docker**: `docker-compose up --build`
3. **Access shell app**: http://localhost:3000
4. **Login with**: admin / admin123

### Development Best Practices

**Module Federation Development:**
- Develop each MF independently when possible
- Use hybrid mode for day-to-day development
- Test production mode before deployment
- Ensure shared dependencies are aligned

**Code Changes Workflow:**
```bash
# For individual MF changes
docker-compose build [mf-name]
docker-compose up [mf-name]

# For multiple changes
docker-compose down
docker-compose up --build
```

**Testing Workflow:**
```bash
# Test all health endpoints
curl http://localhost:3000/health && echo " - Shell: OK"
curl http://localhost:3001/health && echo " - Auth: OK"  
curl http://localhost:3002/health && echo " - Audio: OK"
curl http://localhost:3003/health && echo " - Dashboard: OK"
curl http://localhost:8080/actuator/health && echo " - Backend: OK"
curl http://localhost:8001/health && echo " - Translation: OK"
```

## 📝 Configuration Files

### Key Configuration Files
- **`docker-compose.yml`** - Service orchestration
- **`*/vite.config.ts`** - Module Federation configuration  
- **`*/nginx.conf`** - CORS and routing configuration
- **`application-docker.properties`** - Backend Docker config
- **`package.json`** - Workspace and dependency management

### Environment Variables
- **JWT_SECRET** - JWT token signing secret
- **MYSQL_** - Database configuration variables
- **CORS_ALLOWED_ORIGINS** - Frontend origins for CORS

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Make changes and test**: `docker-compose up --build`
4. **Ensure all health checks pass**
5. **Commit changes**: `git commit -m "Add your feature"`
6. **Push to branch**: `git push origin feature/your-feature`
7. **Create Pull Request**

## 📄 License

This project is licensed under the MIT License.

---

**🚀 Built with Module Federation, React 18, Spring Boot, and Docker**

*Enterprise-ready micro-frontend architecture for scalable web applications*