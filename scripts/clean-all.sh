#!/bin/bash

# Clean All Build Artifacts and Dependencies
set -e

echo "🧹 Cleaning all microfrontends..."
echo "================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to clean a microfrontend
clean_mf() {
    local mf_name=$1
    local mf_dir=$2
    
    echo -e "${BLUE}Cleaning $mf_name...${NC}"
    cd $mf_dir
    
    # Remove build artifacts
    if [ -d "dist" ]; then
        rm -rf dist
        echo -e "${GREEN}  ✅ Removed dist folder${NC}"
    fi
    
    # Remove node_modules if requested
    if [ "$1" = "--deep" ] || [ "$2" = "--deep" ]; then
        if [ -d "node_modules" ]; then
            rm -rf node_modules
            echo -e "${GREEN}  ✅ Removed node_modules${NC}"
        fi
    fi
    
    # Remove Vite cache
    if [ -d "node_modules/.vite" ]; then
        rm -rf node_modules/.vite
        echo -e "${GREEN}  ✅ Removed Vite cache${NC}"
    fi
    
    cd ..
}

# Check for deep clean flag
DEEP_CLEAN=false
if [ "$1" = "--deep" ]; then
    DEEP_CLEAN=true
    echo -e "${YELLOW}🔥 Performing DEEP clean (including node_modules)${NC}"
    echo ""
fi

# Clean root if deep clean
if [ "$DEEP_CLEAN" = true ]; then
    echo -e "${BLUE}Cleaning root directory...${NC}"
    if [ -d "node_modules" ]; then
        rm -rf node_modules
        echo -e "${GREEN}  ✅ Removed root node_modules${NC}"
    fi
fi

# Clean all microfrontends
if [ "$DEEP_CLEAN" = true ]; then
    clean_mf "Shell App" "shell-app" "--deep"
    clean_mf "Auth MF" "auth-mf" "--deep"
    clean_mf "Audio MF" "audio-mf" "--deep"
    clean_mf "Dashboard MF" "dashboard-mf" "--deep"
else
    clean_mf "Shell App" "shell-app"
    clean_mf "Auth MF" "auth-mf"
    clean_mf "Audio MF" "audio-mf"
    clean_mf "Dashboard MF" "dashboard-mf"
fi

echo ""
if [ "$DEEP_CLEAN" = true ]; then
    echo -e "${GREEN}🎉 Deep clean completed! All build artifacts and dependencies removed.${NC}"
    echo ""
    echo "Next steps:"
    echo "• Install dependencies: npm run install:all"
    echo "• Build all: npm run build:all"
else
    echo -e "${GREEN}🎉 Clean completed! All build artifacts removed.${NC}"
    echo ""
    echo "Next steps:"
    echo "• Build all: npm run build:all"
    echo "• For deep clean (including node_modules): npm run clean:all -- --deep"
fi