@echo off
REM Quick start script for Windows Docker Desktop

echo ========================================
echo Robot Tank Docker Launcher
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker is running!
echo.

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env file with your robot's IP address.
    notepad .env
    echo.
)

echo Select which service to run:
echo.
echo 1. Web Robot Controller (Simple Interface - Recommended for 4GB RAM)
echo 2. AVS Robot Dashboard (Advanced 3D Visualization)
echo 3. Both Services (Requires good RAM management)
echo 4. Stop all services
echo 5. Exit
echo.

set /p choice=Enter your choice (1-5):

if "%choice%"=="1" (
    echo.
    echo Starting Web Robot Controller...
    echo Access at: http://localhost:8080
    echo.
    docker-compose up web-robot-controller
) else if "%choice%"=="2" (
    echo.
    echo Starting AVS Robot Dashboard...
    echo Access at: http://localhost:3000
    echo.
    docker-compose up avs-robot-dashboard
) else if "%choice%"=="3" (
    echo.
    echo Starting both services...
    echo Web Robot Controller: http://localhost:8080
    echo AVS Robot Dashboard: http://localhost:3000
    echo.
    echo [WARNING] This may use significant memory on 4GB systems
    timeout /t 3
    docker-compose up
) else if "%choice%"=="4" (
    echo.
    echo Stopping all services...
    docker-compose down
    echo.
    echo All services stopped.
    pause
) else if "%choice%"=="5" (
    echo.
    echo Exiting...
    exit /b 0
) else (
    echo.
    echo Invalid choice. Please run the script again.
    pause
)
