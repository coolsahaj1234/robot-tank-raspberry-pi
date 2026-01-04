#!/bin/bash
# Quick start script for Docker

echo "========================================"
echo "Robot Tank Docker Launcher"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "Docker is running!"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file with your robot's IP address."
    echo "Run: nano .env"
    echo ""
fi

echo "Select which service to run:"
echo ""
echo "1. Web Robot Controller (Simple Interface)"
echo "2. AVS Robot Dashboard (Advanced 3D Visualization)"
echo "3. Both Services"
echo "4. Stop all services"
echo "5. Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Starting Web Robot Controller..."
        echo "Access at: http://localhost:8080"
        echo ""
        docker-compose up web-robot-controller
        ;;
    2)
        echo ""
        echo "Starting AVS Robot Dashboard..."
        echo "Access at: http://localhost:3000"
        echo ""
        docker-compose up avs-robot-dashboard
        ;;
    3)
        echo ""
        echo "Starting both services..."
        echo "Web Robot Controller: http://localhost:8080"
        echo "AVS Robot Dashboard: http://localhost:3000"
        echo ""
        docker-compose up
        ;;
    4)
        echo ""
        echo "Stopping all services..."
        docker-compose down
        echo ""
        echo "All services stopped."
        ;;
    5)
        echo ""
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac
