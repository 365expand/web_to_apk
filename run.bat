@echo off
setlocal enabledelayedexpansion
title WebToAPK Builder - Auto Setup ^& Runner

echo ======================================================================
echo           WebToAPK Builder V1 - Setup ^& Startup Launcher
echo ======================================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] Found: %%i

:: 2. Check Java
echo.
echo [2/5] Checking Java JDK...
where java >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Java not found in PATH!
    if exist "C:\Program Files\Java\jdk-17\bin\java.exe" (
        set "JAVA_HOME=C:\Program Files\Java\jdk-17"
        set "PATH=!JAVA_HOME!\bin;!PATH!"
        echo [OK] Configured JAVA_HOME from C:\Program Files\Java\jdk-17
    ) else (
        echo [ERROR] JDK 17 is required for Android builds.
        pause
        exit /b 1
    )
) else (
    for /f "tokens=*" %%i in ('java -version 2^>^&1 ^| findstr /i "version"') do echo [OK] Found: %%i
)

:: 3. Check Android SDK
echo.
echo [3/5] Checking Android SDK...
if not defined ANDROID_HOME (
    if exist "C:\Android" (
        set "ANDROID_HOME=C:\Android"
        echo [OK] Set ANDROID_HOME to C:\Android
    ) else if exist "%LOCALAPPDATA%\Android\Sdk" (
        set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
        echo [OK] Set ANDROID_HOME to %LOCALAPPDATA%\Android\Sdk
    ) else (
        echo [WARNING] ANDROID_HOME not defined. Builds will require Android SDK.
    )
) else (
    echo [OK] ANDROID_HOME is %ANDROID_HOME%
)

:: 4. Virtual Environment & Dependencies
echo.
echo [4/5] Checking Python Virtual Environment and Dependencies...
cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo [*] Creating virtual environment (backend\venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
)

echo [*] Checking required Python packages...
venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy, PIL, pydantic_settings" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Missing dependencies detected. Installing from requirements.txt...
    venv\Scripts\pip.exe install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requirements!
        pause
        exit /b 1
    )
    echo [OK] All dependencies successfully installed.
) else (
    echo [OK] All Python dependencies are already installed.
)

:: 5. Launch Worker in background window and API in foreground
echo.
echo [5/5] Launching WebToAPK services...
set "PYTHONPATH=%~dp0backend"

echo [*] Starting Build Worker in separate window...
start "WebToAPK - Build Worker" cmd /k "title WebToAPK - Build Worker && cd /d %~dp0backend && set PYTHONPATH=%~dp0backend && venv\Scripts\python.exe -m app.worker"

echo [*] Waiting 2 seconds for worker initialization...
timeout /t 2 /nobreak >nul

echo [*] Opening Web UI in browser (http://localhost:8000)...
start http://localhost:8000

echo [*] Starting API Server on http://127.0.0.1:8000 ...
echo (Press CTRL+C in this window to stop the server)
echo.
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
