@echo off
setlocal

echo =====================================================
echo   🛑 Stopping Robot Tank Controller Services
echo =====================================================
echo.

:: List of ports to clear
set PORTS=3001 3002 5001 5173

for %%P in (%PORTS%) do (
    echo Checking port %%P...
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
        echo Killing process %%a on port %%P...
        taskkill /F /PID %%a >nul 2>&1
    )
)

if exist .pids (
    echo Cleaning up PID file...
    del .pids
)

echo.
echo ✅ All services stopped.
echo =====================================================
pause

endlocal
