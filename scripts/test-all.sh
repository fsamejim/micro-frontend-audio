#!/bin/bash

# Run Tests for All Microfrontends
set -e

echo "🧪 Running tests for all microfrontends..."
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run tests for a microfrontend
test_mf() {
    local mf_name=$1
    local mf_dir=$2
    
    echo -e "${BLUE}Testing $mf_name...${NC}"
    cd $mf_dir
    
    # Check if test script exists
    if npm run | grep -q "test"; then
        if npm run test 2>/dev/null; then
            echo -e "${GREEN}✅ $mf_name tests passed${NC}"
        else
            echo -e "${RED}❌ $mf_name tests failed${NC}"
            TEST_FAILURES=$((TEST_FAILURES + 1))
        fi
    else
        echo -e "${YELLOW}⚠️  $mf_name has no test script${NC}"
    fi
    
    cd ..
    echo ""
}

# Initialize test failure counter
TEST_FAILURES=0

# Test all microfrontends
test_mf "Shell App" "shell-app"
test_mf "Auth MF" "auth-mf"
test_mf "Audio MF" "audio-mf"
test_mf "Dashboard MF" "dashboard-mf"

# Summary
echo -e "${BLUE}Test Summary:${NC}"
if [ $TEST_FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $TEST_FAILURES test suite(s) failed${NC}"
    exit 1
fi