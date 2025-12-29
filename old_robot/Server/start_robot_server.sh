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

# Function to install pigpio from source (fallback)
install_pigpio_from_source() {
    echo -e "${YELLOW}Compiling pigpio from source (this may take a few minutes)...${NC}"
    
    # Install build dependencies
    sudo apt-get install -y build-essential unzip wget
    
    # Create temp directory
    mkdir -p /tmp/pigpio_build
    cd /tmp/pigpio_build
    
    # Download and compile
    echo -e "${YELLOW}Downloading pigpio...${NC}"
    if wget -q https://github.com/joan2937/pigpio/archive/master.zip; then
        unzip -q master.zip
        cd pigpio-master
        echo -e "${YELLOW}Building...${NC}"
        make -j4
        echo -e "${YELLOW}Installing...${NC}"
        sudo make install
        
        # Cleanup
        cd "$SCRIPT_DIR"
        rm -rf /tmp/pigpio_build
        
        echo -e "${GREEN}pigpio installed from source${NC}"
        return 0
    else
        echo -e "${RED}Failed to download pigpio source${NC}"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Function to install missing dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    
    # Check for internet connection
    if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo -e "${RED}Error: No internet connection. Cannot install dependencies.${NC}"
        return 1
    fi

    echo -e "${YELLOW}Updating package list...${NC}"
    sudo apt-get update

    echo -e "${YELLOW}Installing python3-pip...${NC}"
    if ! sudo apt-get install -y python3-pip; then
         echo -e "${RED}Failed to install python3-pip.${NC}"
    fi

    echo -e "${YELLOW}Installing system packages (i2c, smbus)...${NC}"
    # Split installs to prevent one failure from stopping all
    sudo apt-get install -y python3-smbus i2c-tools
    sudo apt-get install -y python3-picamera2
    sudo apt-get install -y unzip wget build-essential

    echo -e "${YELLOW}Attempting to install pigpio...${NC}"
    # Try apt first
    if sudo apt-get install -y pigpio; then
        echo -e "${GREEN}pigpio system package installed${NC}"
    else
        echo -e "${YELLOW}pigpio package not found in apt, attempting build from source...${NC}"
        install_pigpio_from_source
    fi
    
    # Install python3-pigpio (library)
    if ! sudo apt-get install -y python3-pigpio; then
        echo -e "${YELLOW}python3-pigpio not found in apt, installing via pip...${NC}"
        sudo python3 -m pip install pigpio --break-system-packages
    fi

    echo -e "${YELLOW}Installing Python packages...${NC}"
    # rpi-hardware-pwm
    if ! sudo python3 -m pip install rpi_hardware_pwm --break-system-packages; then
        echo -e "${YELLOW}Retrying pip install without break-system-packages flag...${NC}"
        sudo python3 -m pip install rpi_hardware_pwm
    fi

    echo -e "${GREEN}Dependency installation attempt complete.${NC}"
    ldconfig # Refresh library cache for pigpio
    return 0
}

# Function to verify Python dependencies
check_python_deps() {
    echo -e "${YELLOW}Checking Python dependencies...${NC}"
    
    local missing_deps=()
    
    # Check for required Python modules
    python3 -c "import picamera2" 2>/dev/null || missing_deps+=("picamera2")
    python3 -c "import gpiozero" 2>/dev/null || missing_deps+=("gpiozero")
    python3 -c "import pigpio" 2>/dev/null || missing_deps+=("pigpio")
    python3 -c "import smbus" 2>/dev/null || missing_deps+=("smbus")
    python3 -c "import rpi_hardware_pwm" 2>/dev/null || missing_deps+=("rpi_hardware_pwm")
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All Python dependencies are available${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Some Python dependencies may be missing: ${missing_deps[*]}${NC}"
        return 1
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
    
    if [ ! -f "mpu6050.py" ]; then
        echo -e "${RED}✗ mpu6050.py not found${NC}"
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
    
    # Step 2: Check and install dependencies
    if ! command_exists pigpiod || ! check_python_deps; then
        echo -e "${YELLOW}Dependencies missing. Attempting to install...${NC}"
        install_dependencies
    fi

    # Step 3: Start pigpiod
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
