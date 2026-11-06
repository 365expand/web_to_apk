@echo off
title WebToAPK Builder - Auto Setup ^& Runner

echo ======================================================================
echo           WebToAPK Builder V1 - Setup ^& Startup Launcher
echo ======================================================================
echo.

:: 1. Check Python
echo [1/5] Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.12+ from https://www.python.org/ and check "Add Python to PATH".
    goto :error
)
for /f "tokens=*" %%v in ('python --version') do echo [OK] Found: %%v

:: 2. Check Java JDK
echo.
echo [2/5] Checking Java JDK 17...
where java >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files\Java\jdk-17\bin\java.exe" (
        set "JAVA_HOME=C:\Program Files\Java\jdk-17"
        set "PATH=C:\Program Files\Java\jdk-17\bin;%PATH%"
        echo [OK] Configured JAVA_HOME from C:\Program Files\Java\jdk-17
    ) else (
        echo [ERROR] Java JDK 17 is required for Android APK builds.
        goto :error
    )
) else (
    echo [OK] Java is available in PATH.
)

:: 3. Check Android SDK
echo.
echo [3/5] Checking Android SDK...
if "%ANDROID_HOME%"=="" (
    if exist "C:\Android" (
        set "ANDROID_HOME=C:\Android"
        echo [OK] Configured ANDROID_HOME = C:\Android
    ) else if exist "%LOCALAPPDATA%\Android\Sdk" (
        set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
        echo [OK] Configured ANDROID_HOME = %LOCALAPPDATA%\Android\Sdk
    ) else (
        echo [WARNING] ANDROID_HOME is not set. Real builds will require the Android SDK.
    )
) else (
    echo [OK] ANDROID_HOME is %ANDROID_HOME%
)

:: 4. Check & Prepare Virtual Environment and Dependencies
echo.
echo [4/5] Checking Python Virtual Environment and Dependencies...
cd /d "%~dp0backend"
if %errorlevel% neq 0 (
    echo [ERROR] Could not navigate to backend directory: %~dp0backend
    goto :error
)

if not exist "venv\Scripts\python.exe" (
    echo [*] Virtual environment not found. Creating backend\venv ...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        goto :error
    )
    echo [OK] Virtual environment created.
)

echo [*] Verifying installed packages...
venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy, PIL, pydantic_settings" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing required packages from requirements.txt...
    venv\Scripts\pip.exe install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install packages from requirements.txt
        goto :error
    )
    echo [OK] Packages installed successfully.
) else (
    echo [OK] All required packages are already installed.
)

:: 5. Launch Background Worker and API Server
echo.
echo [5/5] Launching WebToAPK services...
set "PYTHONPATH=%~dp0backend"

echo [*] Starting Build Worker process in separate window...
start "WebToAPK - Build Worker" cmd /k "title WebToAPK - Build Worker && cd /d %~dp0backend && set PYTHONPATH=%~dp0backend && venv\Scripts\python.exe -m app.worker"

echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 3 >nul

echo [*] Opening Web UI in your default browser...
start http://localhost:8000

echo.
echo ======================================================================
echo  API Server is running on: http://127.0.0.1:8000
echo  Press CTRL+C in this window at any time to stop the server.
echo ======================================================================
echo.

venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

goto :end

:error
echo.
echo ======================================================================
echo  Startup failed. See the error messages above.
echo ======================================================================
pause
exit /b 1

:end
pause
