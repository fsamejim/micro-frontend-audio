### Quick Guid for setting up all in Mac ###

% cd ~/
% mkdir private
% cd private 
% git clone https://github.com/fsamejim/micro-frontend-audio.git
xcode-select: note: No developer tools were found, requesting install.
If developer tools are located at a non-default location on disk, use `sudo xcode-select --switch path/to/Xcode.app` to specify the Xcode that you wish to use for command line developer tools, and cancel the installation dialog.
See `man xcode-select` for more details.

Install xcode
or

Install Homebrew first (if not already):
% /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Then
% brew install git

% git --version
% git version 2.39.5 (Apple Git-154)


HTTPS should work to clone the repo
at private folder % git clone https://github.com/fsamejim/micro-frontend-audio.git
Cloning into 'micro-frontend-audio'...

private % ls -la
total 0
drwxr-xr-x   3 sammy  staff   96 Feb 12 08:13 .
drwxr-x---+ 15 sammy  staff  480 Feb 12 08:01 ..
drwxr-xr-x  21 sammy  staff  672 Feb 12 08:13 micro-frontend-audio
private % cd micro-frontend-audio 
micro-frontend-audio % git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

micro-frontend-audio % ./setup.sh

==============================================
  Micro-Frontend-Audio Setup
==============================================

  Run './setup.sh --help' for prerequisites

[1/5] Checking prerequisites...

  Docker is not installed (You don't need to login nor register... just download and skip the registration, it should work)

       Docker Desktop is required to run this application.
       Download from: https://docker.com/products/docker-desktop

       Run './setup.sh --help' for full prerequisites info.
  Docker Compose is not available
       Please install Docker Compose or update Docker Desktop

[2/5] Checking port availability...

  Port 3000 (Shell App) is available
  Port 3002 (Auth MF) is available
  Port 3003 (Audio MF) is available
  Port 3004 (Dashboard MF) is available
  Port 8080 (Backend API) is available
  Port 8001 (Translation Service) is available
  Port 3307 (Database) is available

[3/5] Checking environment configuration...

  .env file not found, creating from .env.example...
  Created translation-service/.env
  ASSEMBLYAI_API_KEY needs to be configured
       Get your key from: https://www.assemblyai.com/dashboard
  OPENAI_API_KEY needs to be configured
       Get your key from: https://platform.openai.com/api-keys

  Please edit translation-service/.env and add your API keys

[4/5] Checking Google Cloud credentials...

  Google credentials file not found

       To set up Google Cloud credentials:
       1. Go to https://console.cloud.google.com
       2. Create a project (or select existing)
       3. Enable the 'Cloud Text-to-Speech API'
       4. Go to IAM & Admin > Service Accounts
       5. Create a service account with 'Editor' role
       6. Create a key (JSON format)
       7. Save the downloaded file as:
          translation-service/google-credentials.json


[5/5] Building frontend microfrontends...

  Node.js is not installed
       Node.js is required to build the frontend microfrontends.
       Install via: brew install node
       Or download from: https://nodejs.org

==============================================
  Setup Summary
==============================================

  Setup found 5 issue(s) that need attention.

  Please resolve the issues above and run this script again.

  Quick reference:
    - Prerequisites:  ./setup.sh --help
    - API keys:       Edit translation-service/.env
    - Google creds:   See instructions above
    - Port conflicts: Stop other services using those ports


Step-by-Step Installation (Recommended Way)Download VS Code:Go to the official website: https://code.visualstudio.com/
Click the big Download for macOS button (or go directly to https://code.visualstudio.com/download).

Enable the code Command in TerminalThis lets you open VS Code from Terminal (e.g., code . to open the current folder, or code filename.py).Open VS Code (after step 3 above).
Press Cmd + Shift + P to open the Command Palette.
Type shell command and select Shell Command: Install 'code' command in PATH.
Click OK / confirm.

Look at the .env file in the /micro-frontend-audio/translation-service/.env
# ===================================
# REQUIRED API KEYS
# ===================================

# AssemblyAI API Key (for speech-to-text transcription)
# Get your API key from: https://www.assemblyai.com/dashboard
# Free tier includes up to 460 hours
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# OpenAI API Key (for English to Japanese translation)  
# Get your API key from: https://platform.openai.com/api-keys
# Requires paid plan for reliable usage
OPENAI_API_KEY=sk-your_openai_api_key_here

# Google Cloud Service Account Credentials (for text-to-speech)
# Path to your Google Cloud service account JSON file
# Create service account at: https://console.cloud.google.com/iam-admin/serviceaccounts
GOOGLE_APPLICATION_CREDENTIALS=google-credentials.json


##### Install brew and node
If
% brew install node
zsh: command not found: brew

        Then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        echo >> /Users/sammy/.zprofile
        echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> /Users/sammy/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv zsh)"

        Now it should be
        sammy@H4T26Q3PCGMBP translation-service % brew --version
        Homebrew 5.0.14

% node --version
v25.6.1

### Make sure that .env is saved   Missing API Keys in translation-service/.
Now
    Quick reference:                                                                                                                    
      - Prerequisites:  ./setup.sh --help                                                                                               
      - API keys:       Edit translation-service/.env                                                                                   
      - Google creds:   See instructions above                                                                                          
      - Port conflicts: Stop other services using those ports                                                                           
                                                                                                                                        
./setup.sh

==============================================
  Setup Summary
==============================================

  All checks passed! Your environment is ready.

  To start the application:
    docker-compose up --build

  Access the application at:
    http://localhost:3000

  Start the application now? (y/n): 


initAuth called, token exists:false
No token, setting user to null


Login problem...

npm run build:all     

### Safari Browser has a issue to login ###
⏺ Safari has stricter security for cross-origin storage. Since auth-mf (port 3002) runs inside shell-app (port 3000), Safari may block      
  localStorage access from the microfrontend context.           
                                                                                                                                   
just use Chrome or FireFox

### Maintenance ###

**Default credentials:**
   - Username: `admin`
   - Password: `admin123`

***. Full Production Mode (Testing):***

```bash
npm run prod:local

# Start all services (builds images if needed)
docker-compose up --build

# Start in background
docker-compose up -d

# Stop docker
docker-compose down

### Clean Rebuild Process ###
# Completely delete all data
docker-compose down -v

# Complete clean rebuild (recommended for troubleshooting)
rm -rf */node_modules node_modules
docker system prune -af --volumes

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

