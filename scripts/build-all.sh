#!/bin/bash

# Build All Microfrontends Script
set -e

echo "🔨 Building all microfrontends..."
echo "================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to build a microfrontend
build_mf() {
    local mf_name=$1
    local mf_dir=$2
    
    echo -e "${BLUE}Building $mf_name...${NC}"
    cd $mf_dir
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing dependencies for $mf_name...${NC}"
        npm install
    fi
    
    # Build
    npm run build
    
    # Check if build was successful
    if [ -d "dist" ]; then
        echo -e "${GREEN}✅ $mf_name built successfully${NC}"
    else
        echo -e "${RED}❌ $mf_name build failed${NC}"
        exit 1
    fi
    
    cd ..
}

# Build all microfrontends
build_mf "Shell App" "shell-app"
build_mf "Auth MF" "auth-mf"
build_mf "Audio MF" "audio-mf"
build_mf "Dashboard MF" "dashboard-mf"

echo ""
echo -e "${GREEN}🎉 All microfrontends built successfully!${NC}"
echo ""
echo "You can now:"
echo "• Run locally: npm run dev:local"
echo "• Run in Docker: npm run dev:docker"