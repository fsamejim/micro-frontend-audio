#!/bin/bash

echo "=== Docker Setup Test Script ==="
echo ""

# Check if Docker is running
echo "1. Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi
echo "✅ Docker daemon is running"

# Check Docker Compose
echo ""
echo "2. Checking Docker Compose..."
if ! docker-compose --version >/dev/null 2>&1; then
    echo "❌ Docker Compose not found!"
    exit 1
fi
echo "✅ Docker Compose is available: $(docker-compose --version)"

# Check for port conflicts
echo ""
echo "3. Checking for port conflicts..."
ports=(3000 8080 3307)
conflicts=false

for port in "${ports[@]}"; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is in use:"
        lsof -i :$port
        conflicts=true
    else
        echo "✅ Port $port is available"
    fi
done

if [ "$conflicts" = true ]; then
    echo ""
    echo "⚠️  Some ports are in use. You may need to stop services or change ports in docker-compose.yml"
fi

# Test build (without starting services)
echo ""
echo "4. Testing Docker builds..."

echo "   Building backend..."
if docker-compose build backend >/dev/null 2>&1; then
    echo "✅ Backend build successful"
else
    echo "❌ Backend build failed"
    echo "   Run 'docker-compose build backend' to see detailed error"
fi

echo "   Building frontend..."
if docker-compose build frontend >/dev/null 2>&1; then
    echo "✅ Frontend build successful"
else
    echo "❌ Frontend build failed"
    echo "   Run 'docker-compose build frontend' to see detailed error"
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "To start the full application:"
echo "  docker-compose up --build"
echo ""
echo "To start in background:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"