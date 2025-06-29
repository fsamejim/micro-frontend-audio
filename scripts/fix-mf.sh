#!/bin/bash

# Module Federation Recovery Script
# Use this when you see black screens or Module Federation loading errors

set -e

echo "🔧 Module Federation Recovery Tool"
echo "================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to restart a microfrontend service
restart_mf_service() {
    local mf_name=$1
    local mf_dir=$2
    local port=$3
    
    echo -e "${BLUE}Restarting $mf_name...${NC}"
    
    # Kill existing process
    local existing_pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$existing_pid" ]; then
        echo -e "${YELLOW}Killing existing process on port $port...${NC}"
        kill $existing_pid 2>/dev/null || true
        sleep 2
    fi
    
    # Check if dist folder exists
    if [ ! -d "$mf_dir/dist" ]; then
        echo -e "${YELLOW}No dist folder found, building $mf_name...${NC}"
        cd $mf_dir && npm run build && cd ..
    fi
    
    # Start the service
    echo -e "${BLUE}Starting $mf_name on port $port...${NC}"
    npx serve $mf_dir/dist -p $port --cors > /tmp/${mf_name}-serve.log 2>&1 &
    
    # Wait and validate
    sleep 3
    local mf_url="http://localhost:$port/assets/remoteEntry.js"
    if curl -s -f "$mf_url" > /dev/null; then
        echo -e "${GREEN}✅ $mf_name recovered successfully${NC}"
    else
        echo -e "${RED}❌ $mf_name recovery failed${NC}"
        echo -e "${RED}   Check logs: tail -f /tmp/${mf_name}-serve.log${NC}"
    fi
}

echo -e "${YELLOW}Diagnosing Module Federation issues...${NC}"
echo ""

# Check each microfrontend endpoint
failed_services=()

for service in "auth-mf:3002:Auth-MF" "audio-mf:3003:Audio-MF" "dashboard-mf:3004:Dashboard-MF"; do
    IFS=':' read -r mf_dir port mf_name <<< "$service"
    mf_url="http://localhost:$port/assets/remoteEntry.js"
    
    if ! curl -s -f "$mf_url" > /dev/null 2>&1; then
        echo -e "${RED}❌ $mf_name remoteEntry.js not accessible${NC}"
        failed_services+=("$mf_dir:$port:$mf_name")
    else
        echo -e "${GREEN}✅ $mf_name remoteEntry.js OK${NC}"
    fi
done

if [ ${#failed_services[@]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All Module Federation endpoints are working correctly!${NC}"
    echo ""
    echo "If you're still seeing issues:"
    echo "• Clear browser cache (Ctrl+Shift+R)"
    echo "• Check browser console for other errors"
    echo "• Try: ./scripts/stop-all.sh && ./scripts/dev-local.sh"
    exit 0
fi

echo ""
echo -e "${YELLOW}Found ${#failed_services[@]} failed service(s). Attempting recovery...${NC}"
echo ""

# Restart failed services
for service in "${failed_services[@]}"; do
    IFS=':' read -r mf_dir port mf_name <<< "$service"
    restart_mf_service "$mf_name" "$mf_dir" "$port"
    echo ""
done

echo -e "${BLUE}Recovery complete! Testing all endpoints...${NC}"
echo ""

# Final validation
all_good=true
for service in "auth-mf:3002:Auth-MF" "audio-mf:3003:Audio-MF" "dashboard-mf:3004:Dashboard-MF"; do
    IFS=':' read -r mf_dir port mf_name <<< "$service"
    mf_url="http://localhost:$port/assets/remoteEntry.js"
    
    if curl -s -f "$mf_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $mf_name - Working${NC}"
    else
        echo -e "${RED}❌ $mf_name - Still failed${NC}"
        all_good=false
    fi
done

echo ""
if [ "$all_good" = true ]; then
    echo -e "${GREEN}🎉 Module Federation recovery successful!${NC}"
    echo ""
    echo "Your microfrontends should now work properly:"
    echo "• Dashboard: http://localhost:3000/dashboard"
    echo "• Login: http://localhost:3000/auth/login"
    echo "• Audio: http://localhost:3000/audio"
    echo ""
    echo "Try refreshing your browser (Ctrl+Shift+R)"
else
    echo -e "${RED}❌ Some services still have issues${NC}"
    echo ""
    echo "Next steps:"
    echo "• Check logs in /tmp/ folder"
    echo "• Try: ./scripts/stop-all.sh && ./scripts/dev-local.sh"
    echo "• Rebuild everything: ./scripts/clean-all.sh && ./scripts/build-all.sh"
fi