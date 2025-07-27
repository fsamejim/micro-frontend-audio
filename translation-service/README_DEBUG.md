# Translation Service Debug Guide

Now, I'm going to work on the translation-service I created inside the web app.  
Since it's hard to debug the translation-service itself, I created a debug_workflow.py to go step by step data process.
Here is the debug_workflow.py


This guide helps you debug the translation service step-by-step.

## Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp debug_env.example .env

# Edit .env file with your API keys
nano .env

# Install dependencies
# Optional: Create virtual environment (recommended)
# Install Python 3.12 without affecting system Python
brew update
brew install pyenv

pyenv install 3.12.3

# Set it for your project
cd your-project-folder
pyenv local 3.12.3

# Now this folder uses Python 3.12.3
python --version  # → Python 3.12.3

rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


```

### 2. Run Individual Steps

#### Step 1: Audio Preprocessing
```bash
python debug_workflow.py --step 1 --input path/to/your/audio.mp3

```
**What it does:** Cleans audio and creates 5-minute chunks
**Output:** `debug_output/step1_preprocessing/`

#### Step 2: Transcription  
```bash
python debug_workflow.py --step 2 --input debug_output/step1_preprocessing/processed_audio/chunks
```
**What it does:** Transcribes audio chunks with speaker labels
**Output:** `debug_output/step2_transcription/raw_transcript.txt`

#### Step 3: Text Formatting
```bash
python debug_workflow.py --step 3 --input debug_output/step2_transcription/raw_transcript.txt
```
**What it does:** Formats transcript with proper speaker tags
**Output:** `debug_output/step3_formatting/formatted_transcript.txt`

#### Step 4: Translation
```bash
python debug_workflow.py --step 4 --input debug_output/step3_formatting/formatted_transcript.txt
```
**What it does:** Translates English to Japanese in chunks
**Output:** `debug_output/step4_translation/`

#### Step 5: Chunk Merging
```bash
python debug_workflow.py --step 5 --input debug_output/step4_translation
```
**What it does:** Merges Japanese translation chunks
**Output:** `debug_output/step5_merging/merged_japanese.txt`

#### Step 6: Text Cleaning
```bash
python debug_workflow.py --step 6 --input debug_output/step5_merging/merged_japanese.txt
```
**What it does:** Cleans Japanese text artifacts
**Output:** `debug_output/step6_cleaning/clean_japanese.txt`

#### Step 7: Text-to-Speech
```bash
python debug_workflow.py --step 7 --input debug_output/step6_cleaning/clean_japanese.txt
```
**What it does:** Generates Japanese audio with Google TTS
**Output:** `debug_output/step7_tts/final_japanese_audio.mp3`

### 3. Run Complete Workflow
```bash
python debug_workflow.py --step all --input path/to/your/audio.mp3
```

## Debug Output Structure

```
debug_output/
├── step1_preprocessing/
│   └── processed_audio/
│       ├── {filename}_cleaned.wav
│       └── chunks/
│           ├── chunk_001.wav
│           └── chunk_002.wav
├── step2_transcription/
│   └── raw_transcript.txt
├── step3_formatting/
│   └── formatted_transcript.txt
├── step4_translation/
│   ├── chunk_001.txt
│   └── chunk_002.txt
├── step5_merging/
│   └── merged_japanese.txt
├── step6_cleaning/
│   └── clean_japanese.txt
├── step7_tts/
│   ├── audio_segments/
│   │   ├── segment_0001_Speaker_A.mp3
│   │   └── segment_0002_Speaker_B.mp3
│   └── final_japanese_audio.mp3
└── logs/
```

## Common Issues & Solutions

### Missing API Keys
```
Error: Missing environment variables: ['ASSEMBLYAI_API_KEY']
```
**Solution:** Set environment variables in `.env` file

### Audio Format Issues
```
Error: AudioSegment converter not found
```
**Solution:** Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian  
sudo apt-get install ffmpeg
```

### Google TTS Issues
```
Error: Google Cloud credentials not found
```
**Solution:** Download Google Cloud credentials JSON file and set path in `.env`

## Tips for Debugging

1. **Start with Step 1** - Audio preprocessing is the foundation
2. **Check intermediate files** - Each step produces output you can inspect
3. **Use sample audio** - Start with short 1-2 minute files
4. **Check logs** - Detailed logging shows exactly what's happening
5. **Test individual services** - Isolate issues to specific components

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ASSEMBLYAI_API_KEY` | Yes | For transcription (Steps 2, all) |
| `OPENAI_API_KEY` | Yes | For translation (Steps 4, all) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | For TTS (Steps 7, all) |
| `ASSEMBLYAI_MODEL` | No | Model type: `best` or `nano` |
| `TRANSCRIPTION_RATE_LIMIT_DELAY` | No | Delay between API calls (seconds) |

## Sample Test Audio

Place your test audio files in the root directory:
- `test_short.mp3` (1-2 minutes) - for quick testing
- `test_medium.mp3` (5-10 minutes) - for standard testing  
- `test_long.mp3` (20+ minutes) - for full pipeline testing