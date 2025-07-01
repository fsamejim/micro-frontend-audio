#!/bin/bash

# Local Development Script - Start all microfrontends locally
set -e

echo "🚀 Starting Micro Frontend Audio in LOCAL mode..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Port $port is already in use${NC}"
        echo "Please free up the port or stop conflicting services"
        exit 1
    fi
}

# Function to build microfrontend if needed
build_if_needed() {
    local mf_name=$1
    local mf_dir=$2
    
    if [ ! -d "$mf_dir/dist" ]; then
        echo -e "${YELLOW}Building $mf_name (no dist folder found)...${NC}"
        cd $mf_dir && npm run build && cd ..
    else
        echo -e "${GREEN}$mf_name already built${NC}"
    fi
}

# Function to validate Module Federation endpoint
validate_mf_endpoint() {
    local mf_name=$1
    local port=$2
    local max_attempts=10
    local attempt=1
    
    echo -e "${BLUE}Validating $mf_name Module Federation endpoint...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/assets/remoteEntry.js" > /dev/null; then
            echo -e "${GREEN}✅ $mf_name remoteEntry.js is accessible${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: Waiting for $mf_name...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $mf_name Module Federation endpoint failed validation${NC}"
    echo -e "${RED}   URL: http://localhost:$port/assets/remoteEntry.js${NC}"
    return 1
}

# Function to start and validate a microfrontend service
start_and_validate_mf() {
    local mf_name=$1
    local mf_dir=$2
    local port=$3
    
    echo -e "${BLUE}Starting $mf_name on port $port...${NC}"
    
    # Kill any existing process on the port
    local existing_pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$existing_pid" ]; then
        echo -e "${YELLOW}Killing existing process on port $port (PID: $existing_pid)...${NC}"
        kill $existing_pid 2>/dev/null || true
        sleep 1
    fi
    
    # Start the service in background
    npx serve $mf_dir/dist -p $port --cors > /tmp/${mf_name}-serve.log 2>&1 &
    local serve_pid=$!
    
    # Wait a moment for service to start
    sleep 3
    
    # Validate the Module Federation endpoint
    if validate_mf_endpoint "$mf_name" "$port"; then
        echo -e "${GREEN}✅ $mf_name started successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ $mf_name failed to start properly${NC}"
        echo -e "${RED}   Check logs: tail -f /tmp/${mf_name}-serve.log${NC}"
        kill $serve_pid 2>/dev/null || true
        return 1
    fi
}

echo -e "${BLUE}Checking prerequisites...${NC}"

# Check if all microfrontends have node_modules
for mf in shell-app auth-mf audio-mf dashboard-mf; do
    if [ ! -d "$mf/node_modules" ]; then
        echo -e "${YELLOW}Installing dependencies for $mf...${NC}"
        cd $mf && npm install && cd ..
    fi
done

echo -e "${BLUE}Checking ports availability...${NC}"
check_port 3000  # shell-app
check_port 3002  # auth-mf
check_port 3003  # audio-mf  
check_port 3004  # dashboard-mf

echo -e "${BLUE}Building microfrontends if needed...${NC}"
build_if_needed "Shell App" "shell-app"
build_if_needed "Auth MF" "auth-mf"
build_if_needed "Audio MF" "audio-mf"
build_if_needed "Dashboard MF" "dashboard-mf"

echo -e "${GREEN}Starting all services with validation...${NC}"
echo ""

# Start and validate each microfrontend service
failed_services=0

echo -e "${BLUE}Starting microfrontend services...${NC}"
if ! start_and_validate_mf "Auth-MF" "auth-mf" "3002"; then
    failed_services=$((failed_services + 1))
fi

if ! start_and_validate_mf "Audio-MF" "audio-mf" "3003"; then
    failed_services=$((failed_services + 1))
fi

if ! start_and_validate_mf "Dashboard-MF" "dashboard-mf" "3004"; then
    failed_services=$((failed_services + 1))
fi

# Check if any services failed
if [ $failed_services -gt 0 ]; then
    echo -e "${RED}❌ $failed_services microfrontend service(s) failed to start${NC}"
    echo -e "${RED}Cannot proceed with shell-app startup${NC}"
    echo ""
    echo -e "${YELLOW}To debug:${NC}"
    echo "• Check individual service logs in /tmp/"
    echo "• Run: ./scripts/status.sh"
    echo "• Try: ./scripts/stop-all.sh && ./scripts/dev-local.sh"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All microfrontend services validated successfully!${NC}"
echo ""
echo -e "${BLUE}Starting Shell App (Host)...${NC}"

# Start shell-app last (it depends on the remotes)
echo ""
echo "Services are now available at:"
echo "🏠 Shell App (Host):     http://localhost:3000"
echo "🔐 Auth MF (Remote):     http://localhost:3002 ✅"
echo "🎵 Audio MF (Remote):    http://localhost:3003 ✅"
echo "📊 Dashboard MF (Remote): http://localhost:3004 ✅"
echo ""
echo -e "${YELLOW}Starting Shell App... Press Ctrl+C to stop all services${NC}"
echo ""

# Start shell-app in foreground so user can see logs and stop with Ctrl+C
cd shell-app && npm run dev