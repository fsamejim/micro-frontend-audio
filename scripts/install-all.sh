#!/bin/bash

# Install Dependencies for All Microfrontends
set -e

echo "📦 Installing dependencies for all microfrontends..."
echo "===================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to install dependencies
install_deps() {
    local mf_name=$1
    local mf_dir=$2
    
    echo -e "${BLUE}Installing dependencies for $mf_name...${NC}"
    cd $mf_dir
    
    if [ -f "package.json" ]; then
        npm install
        echo -e "${GREEN}✅ $mf_name dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  No package.json found in $mf_dir${NC}"
    fi
    
    cd ..
}

# Install root dependencies first
echo -e "${BLUE}Installing root dependencies...${NC}"
npm install

# Install for all microfrontends
install_deps "Shell App" "shell-app"
install_deps "Auth MF" "auth-mf"
install_deps "Audio MF" "audio-mf"
install_deps "Dashboard MF" "dashboard-mf"

echo ""
echo -e "${GREEN}🎉 All dependencies installed successfully!${NC}"
echo ""
echo "Next steps:"
echo "• Build all: npm run build:all"
echo "• Start local dev: npm run dev:local"
echo "• Start Docker: npm run dev:docker"