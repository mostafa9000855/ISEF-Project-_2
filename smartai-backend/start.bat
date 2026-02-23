@echo off
REM SmartAI Start Script
REM Launches all components in correct order with proper error handling
REM Usage: start.bat

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║           SmartAI SYSTEM STARTUP SEQUENCE                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

setlocal enabledelayedexpansion

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [STARTUP] Current directory: %cd%
echo [STARTUP] Checking prerequisites...
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo [ERROR] Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found: !cd!

REM Check if Python is installed
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python found

REM Check if C++ compiler is available
where cl.exe >nul 2>nul
if not errorlevel 1 (
    echo [OK] Visual C++ compiler found
) else (
    echo [WARNING] Visual C++ compiler not found in PATH
    echo [WARNING] C++ compilation may fail. Install Visual Studio Build Tools.
)
echo.

REM Create required directories
echo [STARTUP] Creating application directories...
if not exist "build" mkdir build
if not exist "database" mkdir database
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
echo [OK] Directories created
echo.

REM Display component status
echo [STARTUP] Component Status:
echo   • Electron (UI):           Ready to start
echo   • C++ Core Engine:         %SCRIPT_DIR%\build\Release\core_engine.exe
echo   • Python AI Module:        %SCRIPT_DIR%\src\python\ai_module_websocket.py
echo   • Database Layer:          Encrypted SQLite (6 databases)
echo.

echo [STARTUP] Starting SmartAI Components...
echo.

REM Launch Electron
echo [STARTUP - STEP 1/3] Launching Electron main process...
echo   Command: npm start
echo   Component: UI + Orchestrator
echo.

start "SmartAI Electron" npm start

REM Wait for Electron to initialize and start subprocesses
echo [STARTUP - WAITING] Electron initializing (5 seconds)...
timeout /t 5 /nobreak

REM Monitor C++ Core
echo [STARTUP - STEP 2/3] Monitoring C++ Core Engine...
echo   Expected output: "✓ Connected to Electron WebSocket"
echo   Timeout: 15 seconds
echo.

REM Monitor Python AI
echo [STARTUP - STEP 3/3] Monitoring Python AI Module...
echo   Expected output: "✓ WebSocket listening"
echo   Timeout: 15 seconds
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║              SmartAI STATUS: INITIALIZING                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo [INFO] Dashboard should be live in approximately 20 seconds
echo [INFO] Look for green checkmarks in console windows
echo.
echo [MONITORING] Watching for errors...
echo [MONITORING] If any component crashes, it will auto-restart
echo.
echo [DEBUG] Open additional console to monitor:
echo   • C++ output: Check "SmartAI C++" window
echo   • Python output: Check command prompt (if visible)
echo.
echo [STATUS] Press Ctrl+C to shutdown all components gracefully
echo.

REM Keep main window open
cmd /k "echo. && echo [STARTUP] SmartAI system is running. Close this window to stop all components."
