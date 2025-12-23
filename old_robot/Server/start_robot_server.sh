#!/bin/bash
#
# Robot Tank Server Startup Script
# Starts pigpiod daemon and the headless robot server
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Robot Tank Server Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a process is running
is_running() {
    pgrep -f "$1" > /dev/null
}

# Function to start pigpiod
start_pigpiod() {
    echo -e "${YELLOW}Checking pigpiod daemon...${NC}"
    
    if is_running "pigpiod"; then
        echo -e "${GREEN}✓ pigpiod is already running${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Starting pigpiod daemon...${NC}"
    
    # Check if pigpiod binary exists
    if [ -f "/usr/local/bin/pigpiod" ]; then
        PIGPIOD_BIN="/usr/local/bin/pigpiod"
    elif command_exists pigpiod; then
        PIGPIOD_BIN="pigpiod"
    else
        echo -e "${RED}✗ pigpiod binary not found${NC}"
        echo -e "${YELLOW}Attempting to start anyway...${NC}"
        PIGPIOD_BIN="pigpiod"
    fi
    
    # Start pigpiod
    if sudo "$PIGPIOD_BIN" > /dev/null 2>&1; then
        sleep 1
        if is_running "pigpiod"; then
            echo -e "${GREEN}✓ pigpiod started successfully${NC}"
            return 0
        else
            echo -e "${RED}✗ Failed to start pigpiod${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Failed to start pigpiod (may already be running)${NC}"
        # Check again after a moment
        sleep 1
        if is_running "pigpiod"; then
            echo -e "${GREEN}✓ pigpiod is running${NC}"
            return 0
        fi
        return 1
    fi
}

# Function to verify Python dependencies
check_python_deps() {
    echo -e "${YELLOW}Checking Python dependencies...${NC}"
    
    local missing_deps=()
    
    # Check for required Python modules
    python3 -c "import picamera2" 2>/dev/null || missing_deps+=("picamera2")
    python3 -c "import gpiozero" 2>/dev/null || missing_deps+=("gpiozero")
    python3 -c "import pigpio" 2>/dev/null || missing_deps+=("pigpio")
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All Python dependencies are available${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Some Python dependencies may be missing: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}The server will attempt to start anyway...${NC}"
        return 0
    fi
}

# Function to verify server files exist
check_server_files() {
    echo -e "${YELLOW}Checking server files...${NC}"
    
    if [ ! -f "server_headless.py" ]; then
        echo -e "${RED}✗ server_headless.py not found in $SCRIPT_DIR${NC}"
        return 1
    fi
    
    if [ ! -f "servo.py" ]; then
        echo -e "${RED}✗ servo.py not found${NC}"
        return 1
    fi
    
    if [ ! -f "car.py" ]; then
        echo -e "${RED}✗ car.py not found${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ All required server files found${NC}"
    return 0
}

# Main startup sequence
main() {
    echo -e "${YELLOW}Starting startup sequence...${NC}"
    echo ""
    
    # Step 1: Check server files
    if ! check_server_files; then
        echo -e "${RED}Startup aborted: Missing required files${NC}"
        exit 1
    fi
    
    # Step 2: Start pigpiod
    if ! start_pigpiod; then
        echo -e "${YELLOW}⚠ Warning: pigpiod may not be running. Servos may use software PWM (jittery).${NC}"
        echo -e "${YELLOW}Continuing anyway...${NC}"
    fi
    
    # Step 3: Check Python dependencies
    check_python_deps
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Starting Robot Tank Server...${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "Server directory: ${YELLOW}$SCRIPT_DIR${NC}"
    echo -e "Press ${YELLOW}Ctrl+C${NC} to stop the server"
    echo ""
    
    # Step 4: Start the headless server
    # Use sudo for GPIO access
    if sudo python3 server_headless.py; then
        echo ""
        echo -e "${GREEN}Server stopped normally${NC}"
    else
        EXIT_CODE=$?
        echo ""
        echo -e "${RED}Server exited with error code: $EXIT_CODE${NC}"
        exit $EXIT_CODE
    fi
}

# Handle script termination
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    # The server should handle its own cleanup via signal handlers
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run main function
main

