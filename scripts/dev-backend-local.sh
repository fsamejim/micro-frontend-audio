#!/bin/bash

# Local Spring Boot Development Script
set -e

echo "☕ Starting Spring Boot in LOCAL mode..."
echo "======================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Java
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
    echo -e "${GREEN}✅ Java found: $JAVA_VERSION${NC}"
else
    echo -e "${RED}❌ Java not found${NC}"
    echo "Please install Java 21 or newer"
    echo "On macOS: brew install openjdk@21"
    exit 1
fi

# Check Gradle
if [ -f "backend/gradlew" ]; then
    echo -e "${GREEN}✅ Gradle wrapper found${NC}"
elif command_exists gradle; then
    echo -e "${YELLOW}⚠️  Using system Gradle (gradlew preferred)${NC}"
else
    echo -e "${RED}❌ Gradle not found${NC}"
    echo "Please install Gradle or ensure gradlew exists in backend/"
    exit 1
fi

# Check if Spring Boot port is free
if check_port 8080; then
    echo -e "${RED}❌ Port 8080 is already in use${NC}"
    echo "Please stop the existing service or use a different port"
    echo "To check what's using port 8080: lsof -i :8080"
    exit 1
else
    echo -e "${GREEN}✅ Port 8080 is available${NC}"
fi

# Check if Docker MySQL is running
echo -e "${BLUE}Checking database connection...${NC}"
if check_port 3307; then
    echo -e "${GREEN}✅ Docker MySQL appears to be running on port 3307${NC}"
    
    # Test database connection
    if command_exists mysql; then
        echo -e "${BLUE}Testing database connection...${NC}"
        if mysql -h localhost -P 3307 -u sammy -ppassword123 -e "SELECT 1;" audiotranslationdb >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Database connection successful${NC}"
        else
            echo -e "${YELLOW}⚠️  Database connection test failed, but will try anyway${NC}"
            echo -e "${YELLOW}   Spring Boot will show connection errors if database is not ready${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  MySQL client not found, skipping connection test${NC}"
    fi
else
    echo -e "${RED}❌ Docker MySQL not detected on port 3307${NC}"
    echo ""
    echo -e "${YELLOW}To start Docker MySQL:${NC}"
    echo "  docker-compose up database"
    echo "  # OR"
    echo "  npm run dev:backend  # (starts database + other services)"
    echo ""
    echo -e "${YELLOW}Continue anyway? The Spring Boot will fail to start without database.${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Starting Spring Boot with local profile...${NC}"
echo ""
echo "Configuration:"
echo "• Profile: local"
echo "• Port: 8080"  
echo "• Database: Docker MySQL (localhost:3307)"
echo "• Hot reload: enabled"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Change to backend directory
cd backend

# Start Spring Boot with local profile
echo -e "${BLUE}Running: ./gradlew bootRun --args='--spring.profiles.active=local'${NC}"
echo ""

# Use ./gradlew if available, otherwise gradle
if [ -f "./gradlew" ]; then
    ./gradlew bootRun --args='--spring.profiles.active=local'
else
    gradle bootRun --args='--spring.profiles.active=local'
fi