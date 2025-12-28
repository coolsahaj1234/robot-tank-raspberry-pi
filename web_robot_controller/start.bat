@echo off
setlocal

echo =====================================================
echo   🤖 Robot Tank Controller - Windows Startup
echo =====================================================
echo.

:: Check for Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install it from https://nodejs.org/
    pause
    exit /b 1
)

:: Ensure python dependencies are up to date
echo 📦 Checking AI dependencies...
pip install ultralytics >nul 2>&1

:: Run the shared startup logic
node start.js

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Startup failed.
    pause
    exit /b %errorlevel%
)

endlocal
