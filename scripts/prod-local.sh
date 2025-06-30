#!/bin/bash

# Local Production Script - Start all microfrontends in production mode
set -e

echo "🏭 Starting Micro Frontend Audio in FULL PRODUCTION mode..."
echo "========================================================="

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
    
    if [ ! -d "$mf_dir/dist" ] || [ "$mf_dir/src" -nt "$mf_dir/dist" ]; then
        echo -e "${BLUE}Building $mf_name...${NC}"
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
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/assets/remoteEntry.js" > /dev/null; then
            echo -e "${GREEN}✅ $mf_name remoteEntry.js is accessible${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Waiting for $mf_name (attempt $attempt/$max_attempts)...${NC}"
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

# Check if required ports are available
for port in 3000 3002 3003 3004; do
    check_port $port
done

echo -e "${BLUE}Checking ports availability...${NC}"
echo -e "${GREEN}All required ports are available${NC}"

echo -e "${BLUE}Building microfrontends if needed...${NC}"

# Build all microfrontends (including shell-app for production)
build_if_needed "Shell App" "shell-app"
build_if_needed "Auth MF" "auth-mf"
build_if_needed "Audio MF" "audio-mf"
build_if_needed "Dashboard MF" "dashboard-mf"

echo -e "${GREEN}Starting all services with validation...${NC}"
echo ""

# Start microfrontend services in background
echo -e "${BLUE}Starting microfrontend services...${NC}"

failed_services=0

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
    echo "• Try: ./scripts/stop-all.sh && ./scripts/prod-local.sh"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All microfrontend services validated successfully!${NC}"
echo ""
echo -e "${BLUE}Starting Shell App (Host) in PRODUCTION mode...${NC}"

# Start shell-app in production mode (host app - no remoteEntry.js validation)
echo -e "${BLUE}Starting Shell-App on port 3000...${NC}"

# Kill any existing process on port 3000
existing_pid=$(lsof -ti:3000 2>/dev/null || echo "")
if [ -n "$existing_pid" ]; then
    echo -e "${YELLOW}Killing existing process on port 3000 (PID: $existing_pid)...${NC}"
    kill $existing_pid 2>/dev/null || true
    sleep 1
fi

# Start shell-app
npx serve shell-app/dist -p 3000 --cors > /tmp/Shell-App-serve.log 2>&1 &
sleep 3

# Validate shell-app (host app - check main page, not remoteEntry.js)
if curl -s -f "http://localhost:3000" > /dev/null; then
    echo -e "${GREEN}✅ Shell-App started successfully${NC}"
else
    echo -e "${RED}❌ Shell App failed to start properly${NC}"
    echo -e "${RED}   Check logs: tail -f /tmp/Shell-App-serve.log${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All services started successfully in PRODUCTION mode!${NC}"
echo ""
echo "Services are now available at:"
echo "🏠 Shell App (Host):     http://localhost:3000 ✅"
echo "🔐 Auth MF (Remote):     http://localhost:3002 ✅"
echo "🎵 Audio MF (Remote):    http://localhost:3003 ✅"
echo "📊 Dashboard MF (Remote): http://localhost:3004 ✅"
echo ""
echo -e "${BLUE}Production Mode Features:${NC}"
echo "• All services optimized and minified"
echo "• No HTML validation warnings (production React build)"
echo "• Fastest performance"
echo "• Production-ready testing environment"
echo ""
echo -e "${YELLOW}All services running in background. Use Ctrl+C or ./scripts/stop-all.sh to stop${NC}"

# Keep script running so user can stop with Ctrl+C
trap 'echo -e "\n${YELLOW}Stopping all services...${NC}"; ./scripts/stop-all.sh; exit 0' INT

# Wait indefinitely
while true; do
    sleep 10
done