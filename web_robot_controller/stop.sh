#!/bin/bash

# =============================================================================
# Robot Tank Controller - Stop Script
# Stops all running services
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/.pids"

echo -e "${YELLOW}🛑 Stopping Robot Tank Controller services...${NC}"

# Kill by PID file
if [ -f "$PID_FILE" ]; then
    while read pid; do
        if kill -0 $pid 2>/dev/null; then
            echo "Killing PID $pid"
            kill $pid 2>/dev/null || true
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# Kill any processes on our ports
for port in 3001 3002 5001 5173; do
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "Killing processes on port $port: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
done

sleep 1

echo -e "${GREEN}✅ All services stopped${NC}"
