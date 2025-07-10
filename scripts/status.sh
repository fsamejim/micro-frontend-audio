#!/bin/bash

# Check Status of All Services
set -e

echo "📊 Micro Frontend Audio - Service Status"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check port status
check_port_status() {
    local port=$1
    local service_name=$2
    local url="http://localhost:$port"
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name - Running ($url)${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name - Port open but not responding ($url)${NC}"
        fi
    else
        echo -e "${RED}❌ $service_name - Not running${NC}"
    fi
}

# Function to check Module Federation endpoint
check_mf_endpoint() {
    local port=$1
    local service_name=$2
    local mf_url="http://localhost:$port/assets/remoteEntry.js"
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$mf_url" 2>/dev/null)
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✅ $service_name MF - remoteEntry.js accessible${NC}"
        elif [ "$response" = "404" ]; then
            echo -e "${RED}❌ $service_name MF - remoteEntry.js not found (404)${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name MF - remoteEntry.js error (HTTP $response)${NC}"
        fi
    else
        echo -e "${RED}❌ $service_name MF - Service not running${NC}"
    fi
}

# Function to check Docker service status
check_docker_status() {
    local container_name=$1
    local service_name=$2
    
    if command -v docker >/dev/null 2>&1; then
        local status=$(docker ps --filter "name=$container_name" --format "{{.Status}}" 2>/dev/null || echo "")
        if [ -n "$status" ]; then
            echo -e "${GREEN}✅ $service_name (Docker) - $status${NC}"
        else
            echo -e "${RED}❌ $service_name (Docker) - Not running${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Docker not available${NC}"
    fi
}

echo -e "${BLUE}Frontend Services (Local):${NC}"
check_port_status 3000 "Shell App (Host)"
check_port_status 3002 "Auth MF (Remote)"
check_port_status 3003 "Audio MF (Remote)"
check_port_status 3004 "Dashboard MF (Remote)"

echo ""
echo -e "${BLUE}Module Federation Endpoints:${NC}"
check_mf_endpoint 3002 "Auth"
check_mf_endpoint 3003 "Audio"
check_mf_endpoint 3004 "Dashboard"

# Function to check if process is local or Docker
check_process_type() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null || echo "")
    
    if [ -n "$pid" ]; then
        local process_info=$(ps -p $pid -o comm= 2>/dev/null || echo "")
        if [[ "$process_info" == *"java"* ]]; then
            echo "Local Java"
        elif [[ "$process_info" == *"python"* ]]; then
            echo "Local Python"
        elif [[ "$process_info" == *"docker-proxy"* ]] || docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -q ":$port->"; then
            echo "Docker"
        else
            echo "Unknown"
        fi
    else
        echo "Not running"
    fi
}

echo ""
echo -e "${BLUE}Backend Services:${NC}"
spring_boot_type=$(check_process_type 8080)
translation_type=$(check_process_type 8001)
mysql_type=$(check_process_type 3307)

if [ "$spring_boot_type" != "Not running" ]; then
    check_port_status 8080 "Spring Boot API ($spring_boot_type)"
else
    check_port_status 8080 "Spring Boot API"
fi

if [ "$translation_type" != "Not running" ]; then
    check_port_status 8001 "Translation Service ($translation_type)"
else
    check_port_status 8001 "Translation Service"
fi

if [ "$mysql_type" != "Not running" ]; then
    check_port_status 3307 "MySQL Database ($mysql_type)"
else
    check_port_status 3307 "MySQL Database"
fi

echo ""
echo -e "${BLUE}Docker Services:${NC}"
check_docker_status "micro-frontend-audio-backend" "Spring Boot Backend"
check_docker_status "micro-frontend-audio-service" "Translation Service"
check_docker_status "micro-frontend-audio-db" "MySQL Database"

echo ""
echo -e "${BLUE}Build Status:${NC}"
for mf in shell-app auth-mf audio-mf dashboard-mf; do
    if [ -d "$mf/dist" ]; then
        echo -e "${GREEN}✅ $mf - Built${NC}"
    else
        echo -e "${YELLOW}⚠️  $mf - Not built${NC}"
    fi
done

echo ""
echo -e "${BLUE}Dependencies:${NC}"
for mf in shell-app auth-mf audio-mf dashboard-mf; do
    if [ -d "$mf/node_modules" ]; then
        echo -e "${GREEN}✅ $mf - Dependencies installed${NC}"
    else
        echo -e "${RED}❌ $mf - Dependencies missing${NC}"
    fi
done

echo ""
echo -e "${BLUE}Quick Actions:${NC}"
echo "• Install all dependencies: npm run install:all"
echo "• Build all microfrontends: npm run build:all"
echo "• Start hybrid development (recommended): npm run dev:local"
echo "• Start full production locally: npm run prod:local"
echo "• Start Docker services: npm run dev:docker"
echo "• Start local Spring Boot: npm run dev:backend-local"
echo "• Start Docker database only: npm run dev:database"
echo "• Stop all services: npm run stop:all"
echo "• Fix Module Federation issues: npm run fix:mf"