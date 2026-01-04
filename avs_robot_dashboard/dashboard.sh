#!/bin/bash

# AVS Robot Dashboard Management Script
# Comprehensive script for managing the dashboard (install, start, stop, logs, etc.)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="$PROJECT_DIR/logs"

# PID files
BACKEND_PID_FILE="$LOG_DIR/backend.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend.pid"

# Log files
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

#############################################
# Helper Functions
#############################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        return 1
    fi
    return 0
}

#############################################
# Status Functions
#############################################

get_backend_pid() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        cat "$BACKEND_PID_FILE"
    else
        # Try to find by port
        lsof -ti:8081 2>/dev/null || echo ""
    fi
}

get_frontend_pid() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        cat "$FRONTEND_PID_FILE"
    else
        # Try to find by port
        lsof -ti:3000 2>/dev/null || echo ""
    fi
}

is_backend_running() {
    local pid=$(get_backend_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

is_frontend_running() {
    local pid=$(get_frontend_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

#############################################
# Installation Functions
#############################################

install_backend_deps() {
    print_header "Installing Backend Dependencies"

    cd "$BACKEND_DIR"

    # Check Python
    if ! check_command python3; then
        print_error "Python 3 is required"
        exit 1
    fi

    print_info "Python version: $(python3 --version)"

    # Install Python packages
    print_info "Installing Python packages..."

    # Core dependencies
    pip3 install --upgrade pip
    pip3 install opencv-python numpy ultralytics websockets Pillow torch torchvision

    print_success "Core Python packages installed"

    # Optional: Depth Pro
    print_info "Installing Apple Depth Pro (optional, for better depth estimation)..."
    if pip3 install depth-pro 2>/dev/null; then
        print_success "Depth Pro installed"
    else
        print_warning "Depth Pro installation failed (GPU acceleration recommended)"
        print_warning "System will use fallback depth estimation"
    fi

    # Download YOLO models
    print_info "Downloading YOLO models..."
    python3 << EOF
from ultralytics import YOLO
import sys

models = ['yolo11m.pt', 'yolov8x.pt', 'yolov8m.pt']
for model_name in models:
    try:
        print(f"Downloading {model_name}...")
        model = YOLO(model_name)
        print(f"✅ {model_name} ready")
        break  # Stop after first successful download
    except Exception as e:
        print(f"⚠️ Could not download {model_name}: {e}")
        continue
EOF

    print_success "Backend dependencies installed"
}

install_frontend_deps() {
    print_header "Installing Frontend Dependencies"

    cd "$FRONTEND_DIR"

    # Check Node.js
    if ! check_command node; then
        print_error "Node.js is required. Install from https://nodejs.org/"
        exit 1
    fi

    if ! check_command npm; then
        print_error "npm is required"
        exit 1
    fi

    print_info "Node version: $(node --version)"
    print_info "npm version: $(npm --version)"

    # Install npm packages
    print_info "Installing npm packages (this may take a while)..."
    npm install

    print_success "Frontend dependencies installed"
}

install_all() {
    print_header "Installing All Dependencies"

    install_backend_deps
    echo ""
    install_frontend_deps

    echo ""
    print_success "Installation complete!"
    print_info "Run './dashboard.sh start' to launch the dashboard"
}

#############################################
# Start Functions
#############################################

start_backend() {
    if is_backend_running; then
        print_warning "Backend is already running (PID: $(get_backend_pid))"
        return
    fi

    print_info "Starting Backend (XVIZ Server)..."

    cd "$BACKEND_DIR"
    python3 main.py > "$BACKEND_LOG" 2>&1 &
    local pid=$!

    echo "$pid" > "$BACKEND_PID_FILE"

    # Wait and verify it started
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        print_success "Backend started (PID: $pid)"
        print_info "Logs: $BACKEND_LOG"
    else
        print_error "Backend failed to start. Check logs: $BACKEND_LOG"
        rm -f "$BACKEND_PID_FILE"
        exit 1
    fi
}

start_frontend() {
    if is_frontend_running; then
        print_warning "Frontend is already running (PID: $(get_frontend_pid))"
        return
    fi

    print_info "Starting Frontend (React Development Server)..."

    cd "$FRONTEND_DIR"
    BROWSER=none npm start > "$FRONTEND_LOG" 2>&1 &
    local pid=$!

    echo "$pid" > "$FRONTEND_PID_FILE"

    # Wait and verify
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        print_success "Frontend started (PID: $pid)"
        print_info "Logs: $FRONTEND_LOG"
    else
        print_error "Frontend failed to start. Check logs: $FRONTEND_LOG"
        rm -f "$FRONTEND_PID_FILE"
        exit 1
    fi
}

start_all() {
    print_header "Starting AVS Robot Dashboard"

    start_backend
    echo ""
    sleep 2
    start_frontend

    echo ""
    print_success "Dashboard started!"
    print_info "Backend: http://localhost:8081 (WebSocket)"
    print_info "Frontend: http://localhost:3000"
    print_info ""
    print_info "View logs: ./dashboard.sh logs"
    print_info "Stop: ./dashboard.sh stop"
}

#############################################
# Stop Functions
#############################################

stop_backend() {
    local pid=$(get_backend_pid)

    if [ -z "$pid" ]; then
        print_warning "Backend is not running"
        return
    fi

    print_info "Stopping Backend (PID: $pid)..."

    # Try graceful shutdown first
    if kill "$pid" 2>/dev/null; then
        sleep 2

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Backend didn't stop gracefully, force killing..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi

    # Also kill by port
    lsof -ti:8081 | xargs kill -9 2>/dev/null || true

    rm -f "$BACKEND_PID_FILE"
    print_success "Backend stopped"
}

stop_frontend() {
    local pid=$(get_frontend_pid)

    if [ -z "$pid" ]; then
        print_warning "Frontend is not running"
        return
    fi

    print_info "Stopping Frontend (PID: $pid)..."

    # Kill the process tree (npm spawns child processes)
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    sleep 2

    # Force kill if needed
    if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
    fi

    # Also kill by port
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true

    rm -f "$FRONTEND_PID_FILE"
    print_success "Frontend stopped"
}

stop_all() {
    print_header "Stopping AVS Robot Dashboard"

    stop_backend
    stop_frontend

    print_success "Dashboard stopped"
}

#############################################
# Status Function
#############################################

show_status() {
    print_header "Dashboard Status"

    echo ""
    echo "Backend:"
    if is_backend_running; then
        local pid=$(get_backend_pid)
        print_success "Running (PID: $pid)"
        echo "  Port: 8081"
        echo "  Log: $BACKEND_LOG"
    else
        print_error "Not running"
    fi

    echo ""
    echo "Frontend:"
    if is_frontend_running; then
        local pid=$(get_frontend_pid)
        print_success "Running (PID: $pid)"
        echo "  Port: 3000"
        echo "  URL: http://localhost:3000"
        echo "  Log: $FRONTEND_LOG"
    else
        print_error "Not running"
    fi

    echo ""
}

#############################################
# Restart Function
#############################################

restart_all() {
    print_header "Restarting AVS Robot Dashboard"

    stop_all
    echo ""
    sleep 1
    start_all
}

restart_backend() {
    print_header "Restarting Backend"

    stop_backend
    sleep 1
    start_backend
}

restart_frontend() {
    print_header "Restarting Frontend"

    stop_frontend
    sleep 1
    start_frontend
}

#############################################
# Logs Function
#############################################

show_logs() {
    local service="$1"
    local lines="${2:-50}"

    case "$service" in
        backend)
            print_header "Backend Logs (last $lines lines)"
            if [ -f "$BACKEND_LOG" ]; then
                tail -n "$lines" "$BACKEND_LOG"
            else
                print_warning "No backend logs found"
            fi
            ;;
        frontend)
            print_header "Frontend Logs (last $lines lines)"
            if [ -f "$FRONTEND_LOG" ]; then
                tail -n "$lines" "$FRONTEND_LOG"
            else
                print_warning "No frontend logs found"
            fi
            ;;
        *)
            print_header "All Logs (last $lines lines each)"
            echo ""
            echo "=== BACKEND ==="
            if [ -f "$BACKEND_LOG" ]; then
                tail -n "$lines" "$BACKEND_LOG"
            else
                print_warning "No backend logs"
            fi
            echo ""
            echo "=== FRONTEND ==="
            if [ -f "$FRONTEND_LOG" ]; then
                tail -n "$lines" "$FRONTEND_LOG"
            else
                print_warning "No frontend logs"
            fi
            ;;
    esac
}

follow_logs() {
    local service="$1"

    case "$service" in
        backend)
            print_info "Following backend logs (Ctrl+C to stop)..."
            tail -f "$BACKEND_LOG"
            ;;
        frontend)
            print_info "Following frontend logs (Ctrl+C to stop)..."
            tail -f "$FRONTEND_LOG"
            ;;
        *)
            print_info "Following all logs (Ctrl+C to stop)..."
            tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
            ;;
    esac
}

#############################################
# Build Function
#############################################

build_frontend() {
    print_header "Building Frontend for Production"

    cd "$FRONTEND_DIR"

    print_info "Running production build..."
    npm run build

    print_success "Frontend built successfully"
    print_info "Build output: $FRONTEND_DIR/build"
}

#############################################
# Clean Function
#############################################

clean_logs() {
    print_header "Cleaning Logs"

    rm -f "$BACKEND_LOG" "$FRONTEND_LOG"
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"

    print_success "Logs cleaned"
}

#############################################
# Main Command Handler
#############################################

show_help() {
    cat << EOF
AVS Robot Dashboard Management Script

Usage: ./dashboard.sh <command> [options]

Commands:
  install           Install all dependencies (backend + frontend + Depth Pro)

  start             Start both backend and frontend
  start-backend     Start only backend
  start-frontend    Start only frontend

  stop              Stop both backend and frontend
  stop-backend      Stop only backend
  stop-frontend     Stop only frontend

  restart           Restart both services
  restart-backend   Restart only backend
  restart-frontend  Restart only frontend

  status            Show running status of services

  logs [service]    Show logs (backend/frontend/all)
  follow [service]  Follow logs in real-time

  build             Build frontend for production
  clean             Clean log files

  help              Show this help message

Examples:
  ./dashboard.sh install          # First time setup
  ./dashboard.sh start            # Start everything
  ./dashboard.sh logs backend     # View backend logs
  ./dashboard.sh restart-backend  # Restart only backend
  ./dashboard.sh stop             # Stop everything

For more information, see backend/DEPTH_PRO_SETUP.md
EOF
}

#############################################
# Main Script
#############################################

case "${1:-help}" in
    install)
        install_all
        ;;
    start)
        start_all
        ;;
    start-backend)
        start_backend
        ;;
    start-frontend)
        start_frontend
        ;;
    stop)
        stop_all
        ;;
    stop-backend)
        stop_backend
        ;;
    stop-frontend)
        stop_frontend
        ;;
    restart)
        restart_all
        ;;
    restart-backend)
        restart_backend
        ;;
    restart-frontend)
        restart_frontend
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-all}" "${3:-50}"
        ;;
    follow)
        follow_logs "${2:-all}"
        ;;
    build)
        build_frontend
        ;;
    clean)
        clean_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
