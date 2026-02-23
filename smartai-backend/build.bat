@echo off
REM SmartAI Build Script
REM Builds C++ components, Python packages, and creates installer
REM Usage: build.bat [dev|prod]

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║           SmartAI BUILD & PACKAGING SYSTEM                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

setlocal enabledelayedexpansion

set BUILD_MODE=%1
if "%BUILD_MODE%"=="" set BUILD_MODE=prod

if not "%BUILD_MODE%"=="dev" if not "%BUILD_MODE%"=="prod" (
    echo [ERROR] Invalid build mode. Usage: build.bat [dev^|prod]
    exit /b 1
)

echo [BUILD] Mode: %BUILD_MODE%
echo [BUILD] Target OS: Windows 10/11 x64
echo [BUILD] Architecture: Electron + C++ Core + Python AI
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM ==================== STEP 1: SETUP ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║ STEP 1: ENVIRONMENT SETUP                                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

if not exist "build" mkdir build
echo [OK] Build directory exists

if not exist "node_modules" (
    echo [BUILD] Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed
        exit /b 1
    )
    echo [OK] npm modules installed
) else (
    echo [OK] npm modules already installed
)
echo.

REM ==================== STEP 2: BUILD C++ ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║ STEP 2: COMPILE C++ CORE ENGINE                           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

cd /d "%SCRIPT_DIR%\build"

if "%BUILD_MODE%"=="dev" (
    echo [BUILD] Building C++ with DEBUG symbols...
    call cmake .. -DCMAKE_BUILD_TYPE=Debug
) else (
    echo [BUILD] Building C++ with OPTIMIZATIONS...
    call cmake .. -DCMAKE_BUILD_TYPE=Release
)

if errorlevel 1 (
    echo [ERROR] CMake configuration failed
    exit /b 1
)
echo [OK] CMake configured

call cmake --build . --config %BUILD_MODE% --parallel 4
if errorlevel 1 (
    echo [ERROR] C++ compilation failed
    exit /b 1
)
echo [OK] C++ Core Engine compiled successfully
echo.

cd /d "%SCRIPT_DIR%"

REM ==================== STEP 3: BUILD PYTHON ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║ STEP 3: INSTALL PYTHON DEPENDENCIES                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo [BUILD] Installing Python packages...
call pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Python package installation failed
    exit /b 1
)
echo [OK] Python modules installed
echo.

REM ==================== STEP 4: BUILD ELECTRON ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║ STEP 4: BUILD ELECTRON APPLICATION                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

if "%BUILD_MODE%"=="dev" (
    echo [BUILD] Building for development...
    echo [INFO] Using dev symbols and debug logging
) else (
    echo [BUILD] Building for production...
    echo [INFO] Creating signed installer...
)

call npm run build-electron
if errorlevel 1 (
    echo [ERROR] Electron build failed
    exit /b 1
)
echo [OK] Electron build complete
echo.

REM ==================== STEP 5: VERIFY BUILD ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║ STEP 5: VERIFY BUILD ARTIFACTS                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

set CORE_EXE=build\%BUILD_MODE%\core_engine.exe
set INSTALLER=dist\SmartAI-Setup-1.0.0.exe

if exist "%CORE_EXE%" (
    echo [OK] C++ Core Engine: %CORE_EXE%
    for %%F in ("%CORE_EXE%") do echo     Size: %%~zF bytes
) else (
    echo [ERROR] C++ Core Engine not found: %CORE_EXE%
)

if exist "%INSTALLER%" (
    echo [OK] Windows Installer: %INSTALLER%
    for %%F in ("%INSTALLER%") do echo     Size: %%~zF bytes
) else (
    echo [WARNING] Installer not found yet: %INSTALLER%
)

echo.

REM ==================== BUILD COMPLETE ====================
echo ╔════════════════════════════════════════════════════════════╗
echo ║              BUILD COMPLETE - %BUILD_MODE% MODE                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

if "%BUILD_MODE%"=="dev" (
    echo [NEXT] To start development:
    echo   # npm start
    echo   OR
    echo   # start.bat
    echo.
) else (
    echo [NEXT] To install:
    echo   # %INSTALLER%
    echo.
    echo [NEXT] To package further:
    echo   # electron-builder --publish never
    echo.
)

echo [INFO] Build artifacts in:
echo   • C++: %SCRIPT_DIR%\build\%BUILD_MODE%
echo   • Electron: %SCRIPT_DIR%\dist
echo   • Installer: %SCRIPT_DIR%\dist\SmartAI-Setup-1.0.0.exe
echo.

echo [SUCCESS] SmartAI build completed successfully!
echo.
pause
