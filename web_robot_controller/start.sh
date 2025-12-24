#!/bin/bash

# =============================================================================
# Robot Tank Controller - Startup Script
# Starts all services: Node.js bridge, React frontend, Python AI service
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# PID file for tracking background processes
PID_FILE="$SCRIPT_DIR/.pids"

# =============================================================================
# Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}=====================================================${NC}"
    echo -e "${CYAN}  🤖 Robot Tank Controller - Startup${NC}"
    echo -e "${CYAN}=====================================================${NC}"
    echo ""
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

kill_port() {
    local port=$1
    if port_in_use $port; then
        echo -e "${YELLOW}Killing process on port $port...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"

    # Kill processes by PID file
    if [ -f "$PID_FILE" ]; then
        while read pid; do
            if kill -0 $pid 2>/dev/null; then
                kill $pid 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi

    # Kill any remaining processes on our ports
    for port in 3001 3002 5001 5173; do
        kill_port $port
    done

    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set up trap for cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

    # Check Node.js
    if ! command_exists node; then
        echo -e "${RED}❌ Node.js is not installed${NC}"
        echo -e "   Install with: brew install node"
        exit 1
    fi
    echo -e "${GREEN}✅ Node.js $(node --version)${NC}"

    # Check npm
    if ! command_exists npm; then
        echo -e "${RED}❌ npm is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ npm $(npm --version)${NC}"

    # Check Python 3
    if ! command_exists python3; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        echo -e "   Install with: brew install python3"
        exit 1
    fi
    echo -e "${GREEN}✅ $(python3 --version)${NC}"

    # Check pip3
    if ! command_exists pip3; then
        echo -e "${RED}❌ pip3 is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ pip3 installed${NC}"

    echo ""
}

get_port_service() {
    case $1 in
        3001) echo "Bridge HTTP" ;;
        3002) echo "Bridge WebSocket" ;;
        5001) echo "AI Service" ;;
        5173) echo "React Frontend" ;;
        *) echo "Unknown" ;;
    esac
}

check_ports() {
    echo -e "${YELLOW}🔌 Checking ports...${NC}"

    local ports_blocked=false

    for port in 3001 3002 5001 5173; do
        local service_name=$(get_port_service $port)
        if port_in_use $port; then
            echo -e "${RED}❌ Port $port ($service_name) is in use${NC}"
            ports_blocked=true
        else
            echo -e "${GREEN}✅ Port $port ($service_name) available${NC}"
        fi
    done

    if [ "$ports_blocked" = true ]; then
        echo ""
        echo -n "Kill existing processes on these ports? (y/n) "
        read -r REPLY
        if [ "$REPLY" = "y" ] || [ "$REPLY" = "Y" ]; then
            for port in 3001 3002 5001 5173; do
                kill_port $port
            done
            echo -e "${GREEN}✅ Ports cleared${NC}"
        else
            echo -e "${RED}Cannot start with ports in use. Exiting.${NC}"
            exit 1
        fi
    fi

    echo ""
}

install_dependencies() {
    # Install root Node.js dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
        npm install
        echo ""
    fi

    # Install React client dependencies
    if [ ! -d "client/node_modules" ]; then
        echo -e "${YELLOW}📦 Installing React client dependencies...${NC}"
        cd client && npm install && cd ..
        echo ""
    fi

    # Setup Python virtual environment
    if [ ! -d "ai_service/venv" ]; then
        echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
        cd ai_service
        python3 -m venv venv
        cd ..
        echo ""
    fi

    # Install Python dependencies
    echo -e "${YELLOW}🐍 Checking Python dependencies...${NC}"
    cd ai_service
    source venv/bin/activate

    # Check if key packages are installed
    if ! python3 -c "import cv2, flask, numpy" 2>/dev/null; then
        echo -e "${YELLOW}📦 Installing Python AI service dependencies...${NC}"
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo -e "${GREEN}✅ Python dependencies installed${NC}"
    fi

    deactivate
    cd ..
    echo ""
}

start_services() {
    echo -e "${GREEN}🚀 Starting all services...${NC}"
    echo ""

    # Create logs directory
    mkdir -p logs

    # Clear PID file
    > "$PID_FILE"

    # Start Bridge Server
    echo -e "${BLUE}Starting Bridge Server...${NC}"
    node server/index.js > logs/bridge.log 2>&1 &
    echo $! >> "$PID_FILE"
    sleep 1

    if port_in_use 3001; then
        echo -e "${GREEN}✅ Bridge Server running on port 3001/3002${NC}"
    else
        echo -e "${RED}❌ Bridge Server failed to start. Check logs/bridge.log${NC}"
        exit 1
    fi

    # Start AI Service
    echo -e "${BLUE}Starting AI Service...${NC}"
    cd ai_service
    source venv/bin/activate
    python3 server.py > ../logs/ai_service.log 2>&1 &
    AI_PID=$!
    echo $AI_PID >> "$PID_FILE"
    deactivate
    cd ..

    # Wait for AI service to start (up to 5 seconds)
    for i in 1 2 3 4 5; do
        sleep 1
        if port_in_use 5001; then
            echo -e "${GREEN}✅ AI Service running on port 5001${NC}"
            break
        fi
        if [ $i -eq 5 ]; then
            echo -e "${RED}❌ AI Service failed to start. Check logs/ai_service.log${NC}"
            cat logs/ai_service.log 2>/dev/null | tail -10
            exit 1
        fi
    done

    # Start React Frontend
    echo -e "${BLUE}Starting React Frontend...${NC}"
    cd client
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID >> "$PID_FILE"
    cd ..

    # Wait for frontend to start (up to 10 seconds - Vite can take a moment)
    echo -n "   Waiting for Vite..."
    for i in 1 2 3 4 5 6 7 8 9 10; do
        sleep 1
        if port_in_use 5173; then
            echo ""
            echo -e "${GREEN}✅ React Frontend running on port 5173${NC}"
            break
        fi
        echo -n "."
        if [ $i -eq 10 ]; then
            echo ""
            echo -e "${RED}❌ React Frontend failed to start. Check logs/frontend.log${NC}"
            cat logs/frontend.log 2>/dev/null | tail -10
            exit 1
        fi
    done

    echo ""
}

print_status() {
    echo -e "${CYAN}=====================================================${NC}"
    echo -e "${GREEN}  ✅ All services are running!${NC}"
    echo -e "${CYAN}=====================================================${NC}"
    echo ""
    echo -e "${BLUE}📱 Access the application:${NC}"
    echo -e "   ${GREEN}http://localhost:5173${NC}"
    echo ""
    echo -e "${BLUE}📡 Service endpoints:${NC}"
    echo -e "   • Frontend:  ${CYAN}http://localhost:5173${NC}"
    echo -e "   • Bridge:    ${CYAN}http://localhost:3001${NC} (HTTP)"
    echo -e "   • Bridge:    ${CYAN}ws://localhost:3002${NC} (WebSocket)"
    echo -e "   • AI:        ${CYAN}http://localhost:5001${NC}"
    echo ""
    echo -e "${BLUE}📁 Log files:${NC}"
    echo -e "   • logs/bridge.log"
    echo -e "   • logs/ai_service.log"
    echo -e "   • logs/frontend.log"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

print_header
check_prerequisites
check_ports
install_dependencies
start_services
print_status

# Keep script running and wait for all background processes
wait
