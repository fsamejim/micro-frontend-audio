#!/bin/bash

# =============================================================================
# Micro-Frontend-Audio Setup Script
# =============================================================================
# This script helps new users set up the application after cloning the repo.
# Run this script before running docker-compose up.
#
# Usage:
#   ./setup.sh              Full setup with port check and launch option
#   ./setup.sh --check-only Validate config only (skip ports, no launch prompt)
#   ./setup.sh --help       Show prerequisites and usage information
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to show prerequisites
show_prerequisites() {
    echo ""
    echo -e "${BOLD}=============================================="
    echo "  Prerequisites"
    echo -e "==============================================${NC}"
    echo ""
    echo -e "${BOLD}DOCKER DEPLOYMENT (Recommended - Easiest)${NC}"
    echo ""
    echo "  Only ONE thing to install:"
    echo ""
    echo -e "  ${GREEN}Docker Desktop${NC}"
    echo "    Download: https://docker.com/products/docker-desktop"
    echo ""
    echo "  That's it! Everything else runs in containers:"
    echo "  Node.js, Java 21, Python 3.11, MySQL 8.0, FFmpeg"
    echo ""
    echo "-------------------------------------------"
    echo ""
    echo -e "${BOLD}LOCAL DEVELOPMENT (Without Docker)${NC}"
    echo ""
    echo "  If you want to run services directly on your Mac:"
    echo ""
    echo "  Install                Version      Purpose"
    echo "  --------------------   ----------   ----------------------"
    echo "  Node.js                >= 18.0.0    Frontend microfrontends"
    echo "  npm                    >= 8.0.0     Package management"
    echo "  Java JDK               21           Spring Boot backend"
    echo "  Python                 3.11         Translation service"
    echo "  FFmpeg                 Latest       Audio processing"
    echo "  MySQL                  8.0          Database"
    echo ""
    echo "  Install via Homebrew:"
    echo "    brew install node@18"
    echo "    brew install openjdk@21"
    echo "    brew install python@3.11"
    echo "    brew install ffmpeg"
    echo "    brew install mysql"
    echo ""
    echo "-------------------------------------------"
    echo ""
    echo -e "${BOLD}REQUIRED API KEYS${NC}"
    echo ""
    echo "  You will need these API keys (free tiers available):"
    echo ""
    echo "  1. AssemblyAI (Speech-to-Text)"
    echo "     Sign up: https://www.assemblyai.com"
    echo "     Free tier: 460 hours of transcription"
    echo ""
    echo "  2. OpenAI (Translation)"
    echo "     Sign up: https://platform.openai.com"
    echo "     Requires billing setup"
    echo ""
    echo "  3. Google Cloud (Text-to-Speech)"
    echo "     Console: https://console.cloud.google.com"
    echo "     Enable: Cloud Text-to-Speech API"
    echo "     Create: Service account with JSON key"
    echo ""
}

# Function to show usage
show_usage() {
    echo ""
    echo -e "${BOLD}Usage:${NC}"
    echo "  ./setup.sh              Full setup with port check and launch option"
    echo "  ./setup.sh --check-only Validate config only (skip ports, no launch)"
    echo "  ./setup.sh --help       Show prerequisites and usage information"
    echo ""
}

# Parse arguments
CHECK_ONLY=false
SHOW_HELP=false

if [ "$1" = "--check-only" ]; then
    CHECK_ONLY=true
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    SHOW_HELP=true
fi

# Show help and exit if requested
if [ "$SHOW_HELP" = true ]; then
    show_prerequisites
    show_usage
    exit 0
fi

# Track overall status
SETUP_ISSUES=0

echo ""
echo "=============================================="
echo "  Micro-Frontend-Audio Setup"
if [ "$CHECK_ONLY" = true ]; then
    echo "  (Check-only mode)"
fi
echo "=============================================="
echo ""
echo "  Run './setup.sh --help' for prerequisites"
echo ""

# =============================================================================
# 1. Prerequisites Check
# =============================================================================
echo -e "${BLUE}[1/4] Checking prerequisites...${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}  Docker is not installed${NC}"
    echo ""
    echo "       Docker Desktop is required to run this application."
    echo "       Download from: https://docker.com/products/docker-desktop"
    echo ""
    echo "       Run './setup.sh --help' for full prerequisites info."
    SETUP_ISSUES=$((SETUP_ISSUES + 1))
else
    if ! docker info &> /dev/null; then
        echo -e "${RED}  Docker is installed but not running${NC}"
        echo "       Please start Docker Desktop and run this script again"
        SETUP_ISSUES=$((SETUP_ISSUES + 1))
    else
        echo -e "${GREEN}  Docker is running${NC}"
        docker --version | sed 's/^/       /'
    fi
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    # Try docker compose (newer syntax)
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}  Docker Compose is not available${NC}"
        echo "       Please install Docker Compose or update Docker Desktop"
        SETUP_ISSUES=$((SETUP_ISSUES + 1))
    else
        echo -e "${GREEN}  Docker Compose is available (docker compose)${NC}"
        docker compose version | sed 's/^/       /'
    fi
else
    echo -e "${GREEN}  Docker Compose is available${NC}"
    docker-compose --version | sed 's/^/       /'
fi

echo ""

# =============================================================================
# 2. Port Availability Check
# =============================================================================
if [ "$CHECK_ONLY" = true ]; then
    echo -e "${BLUE}[2/4] Skipping port check (--check-only mode)${NC}"
    echo ""
else
    echo -e "${BLUE}[2/4] Checking port availability...${NC}"
    echo ""

    PORTS=(
        "3000:Shell App"
        "3002:Auth MF"
        "3003:Audio MF"
        "3004:Dashboard MF"
        "8080:Backend API"
        "8001:Translation Service"
        "3307:Database"
    )

    PORT_CONFLICTS=0
    for port_entry in "${PORTS[@]}"; do
        PORT="${port_entry%%:*}"
        SERVICE="${port_entry#*:}"

        if lsof -Pi :$PORT -sTCP:LISTEN -t &> /dev/null; then
            echo -e "${YELLOW}  Port $PORT ($SERVICE) is in use${NC}"
            PORT_CONFLICTS=$((PORT_CONFLICTS + 1))
        else
            echo -e "${GREEN}  Port $PORT ($SERVICE) is available${NC}"
        fi
    done

    if [ $PORT_CONFLICTS -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}  Warning: $PORT_CONFLICTS port(s) are in use${NC}"
        echo "       You may need to stop other services before running the app"
        SETUP_ISSUES=$((SETUP_ISSUES + 1))
    fi

    echo ""
fi

# =============================================================================
# 3. Environment File Setup
# =============================================================================
echo -e "${BLUE}[3/4] Checking environment configuration...${NC}"
echo ""

ENV_FILE="translation-service/.env"
ENV_EXAMPLE="translation-service/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        echo -e "${YELLOW}  .env file not found, creating from .env.example...${NC}"
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "${GREEN}  Created $ENV_FILE${NC}"
    else
        echo -e "${RED}  Neither .env nor .env.example found!${NC}"
        SETUP_ISSUES=$((SETUP_ISSUES + 1))
    fi
else
    echo -e "${GREEN}  .env file exists${NC}"
fi

# Check for placeholder API keys
if [ -f "$ENV_FILE" ]; then
    ASSEMBLYAI_KEY=$(grep "^ASSEMBLYAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    OPENAI_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)

    API_KEY_ISSUES=0

    if [ -z "$ASSEMBLYAI_KEY" ] || [ "$ASSEMBLYAI_KEY" = "your_assemblyai_api_key_here" ]; then
        echo -e "${YELLOW}  ASSEMBLYAI_API_KEY needs to be configured${NC}"
        echo "       Get your key from: https://www.assemblyai.com/dashboard"
        API_KEY_ISSUES=$((API_KEY_ISSUES + 1))
    else
        echo -e "${GREEN}  ASSEMBLYAI_API_KEY is configured${NC}"
    fi

    if [ -z "$OPENAI_KEY" ] || [[ "$OPENAI_KEY" == sk-your* ]]; then
        echo -e "${YELLOW}  OPENAI_API_KEY needs to be configured${NC}"
        echo "       Get your key from: https://platform.openai.com/api-keys"
        API_KEY_ISSUES=$((API_KEY_ISSUES + 1))
    else
        echo -e "${GREEN}  OPENAI_API_KEY is configured${NC}"
    fi

    if [ $API_KEY_ISSUES -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}  Please edit $ENV_FILE and add your API keys${NC}"
        SETUP_ISSUES=$((SETUP_ISSUES + 1))
    fi
fi

echo ""

# =============================================================================
# 4. Google Credentials Setup
# =============================================================================
echo -e "${BLUE}[4/4] Checking Google Cloud credentials...${NC}"
echo ""

GOOGLE_CREDS="translation-service/google-credentials.json"
GOOGLE_CREDS_EXAMPLE="translation-service/google-credentials.json.example"

if [ -d "$GOOGLE_CREDS" ]; then
    # It's a directory (Docker artifact) - this is a common problem
    echo -e "${RED}  $GOOGLE_CREDS is a directory (not a file)${NC}"
    echo "       This happens when Docker runs before the file exists."
    echo ""
    read -p "       Remove this directory? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$GOOGLE_CREDS"
        echo -e "${GREEN}  Directory removed${NC}"
    fi
    SETUP_ISSUES=$((SETUP_ISSUES + 1))
elif [ -f "$GOOGLE_CREDS" ]; then
    # Check if it's valid JSON with required field
    if python3 -c "import json; json.load(open('$GOOGLE_CREDS'))" 2>/dev/null; then
        if grep -q '"type": "service_account"' "$GOOGLE_CREDS"; then
            echo -e "${GREEN}  Google credentials file exists and appears valid${NC}"
        else
            echo -e "${YELLOW}  Google credentials file exists but may not be a service account key${NC}"
            SETUP_ISSUES=$((SETUP_ISSUES + 1))
        fi
    else
        echo -e "${RED}  Google credentials file exists but is not valid JSON${NC}"
        SETUP_ISSUES=$((SETUP_ISSUES + 1))
    fi
else
    echo -e "${YELLOW}  Google credentials file not found${NC}"
    echo ""
    echo "       To set up Google Cloud credentials:"
    echo "       1. Go to https://console.cloud.google.com"
    echo "       2. Create a project (or select existing)"
    echo "       3. Enable the 'Cloud Text-to-Speech API'"
    echo "       4. Go to IAM & Admin > Service Accounts"
    echo "       5. Create a service account with 'Editor' role"
    echo "       6. Create a key (JSON format)"
    echo "       7. Save the downloaded file as:"
    echo "          $GOOGLE_CREDS"
    echo ""
    SETUP_ISSUES=$((SETUP_ISSUES + 1))
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo "=============================================="
echo "  Setup Summary"
echo "=============================================="
echo ""

if [ $SETUP_ISSUES -eq 0 ]; then
    echo -e "${GREEN}  All checks passed! Your environment is ready.${NC}"
    echo ""

    if [ "$CHECK_ONLY" = true ]; then
        echo "  Configuration validated successfully."
        echo ""
    else
        echo "  To start the application:"
        echo "    docker-compose up --build"
        echo ""
        echo "  Or start in background:"
        echo "    docker-compose up -d --build"
        echo ""

        read -p "  Start the application now? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "Starting application..."
            docker-compose up --build
        fi
    fi
else
    echo -e "${YELLOW}  Setup found $SETUP_ISSUES issue(s) that need attention.${NC}"
    echo ""
    echo "  Please resolve the issues above and run this script again."
    echo ""
    echo "  Quick reference:"
    echo "    - Prerequisites:  ./setup.sh --help"
    echo "    - API keys:       Edit translation-service/.env"
    echo "    - Google creds:   See instructions above"
    echo "    - Port conflicts: Stop other services using those ports"
    echo ""
fi
