#!/bin/bash

# Stop All Running Services (Local and Docker)
set -e

echo "🛑 Stopping all Micro Frontend Audio services..."
echo "==============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Stopping $service_name on port $port (PID: $pid)...${NC}"
        kill $pid 2>/dev/null || echo -e "${RED}Failed to kill PID $pid${NC}"
        sleep 1
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            echo -e "${RED}Force killing $service_name...${NC}"
            kill -9 $pid 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ $service_name stopped${NC}"
    else
        echo -e "${BLUE}$service_name not running on port $port${NC}"
    fi
}

echo -e "${BLUE}Stopping local development servers...${NC}"
# Stop local microfrontend servers
kill_port 3000 "Shell App"
kill_port 3002 "Auth MF"
kill_port 3003 "Audio MF" 
kill_port 3004 "Dashboard MF"

echo ""
echo -e "${BLUE}Stopping Docker services...${NC}"
# Stop Docker services
if command -v docker-compose >&2; then
    if [ -f "docker-compose.yml" ]; then
        docker-compose down 2>/dev/null || echo -e "${YELLOW}No Docker services to stop${NC}"
        echo -e "${GREEN}✅ Docker services stopped${NC}"
    else
        echo -e "${YELLOW}No docker-compose.yml found${NC}"
    fi
else
    echo -e "${YELLOW}Docker Compose not installed${NC}"
fi

echo ""
echo -e "${BLUE}Stopping any remaining Node processes...${NC}"
# Kill any remaining node processes related to our project
pkill -f "vite" 2>/dev/null || echo -e "${BLUE}No Vite processes found${NC}"
pkill -f "serve.*3002\|serve.*3003\|serve.*3004" 2>/dev/null || echo -e "${BLUE}No serve processes found${NC}"

echo ""
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo ""
echo "To start services again:"
echo "• Local mode: npm run dev:local"
echo "• Docker mode: npm run dev:docker"