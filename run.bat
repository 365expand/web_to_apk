@echo off
title WebToNative Studio - All-in-One Local Runner

echo ======================================================================
echo           WebToNative Studio - Setup ^& Full-Stack Launcher
echo ======================================================================
echo.

:: 1. Check Python
echo [1/6] Checking Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.12+ from https://www.python.org/ and check "Add Python to PATH".
    goto :error
)
for /f "tokens=*" %%v in ('python --version') do echo [OK] Found: %%v

:: 2. Check Node.js & npm (for Next.js Frontend)
echo.
echo [2/6] Checking Node.js ^& npm for Next.js frontend...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in your PATH.
    echo Please install Node.js 18+ from https://nodejs.org/ to run the Next.js frontend.
    goto :error
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is not found.
    goto :error
)
for /f "tokens=*" %%v in ('node -v') do echo [OK] Node.js: %%v
for /f "tokens=*" %%v in ('npm -v') do echo [OK] npm: %%v

:: 3. Check Java JDK
echo.
echo [3/6] Checking Java JDK 17...
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

:: 4. Check Android SDK
echo.
echo [4/6] Checking Android SDK...
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

:: 5. Check & Prepare Backend Dependencies
echo.
echo [5/6] Checking Backend Python environment...
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

echo [*] Verifying backend installed packages...
venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy, PIL, pydantic_settings, redis" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing required backend packages...
    venv\Scripts\pip.exe install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install packages from requirements.txt
        goto :error
    )
    echo [OK] Backend packages installed successfully.
) else (
    echo [OK] Backend packages ready.
)

:: 6. Check & Prepare Frontend (Next.js)
echo.
echo [6/6] Checking Next.js Frontend dependencies...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo [*] Installing frontend npm packages - please wait...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed in frontend.
        goto :error
    )
    echo [OK] Frontend packages installed.
) else (
    echo [OK] Frontend packages ready.
)

:: Launch All Services
echo.
echo ======================================================================
echo  Launching WebToNative Full-Stack:
echo   1. Background Build Worker Process
echo   2. Next.js Frontend on http://localhost:3000
echo   3. FastAPI API Server on http://127.0.0.1:8000
echo ======================================================================
echo.

set "PYTHONPATH=%~dp0backend"

echo [*] Starting Build Worker process...
start "WebToNative - Build Worker" cmd /k "title WebToNative - Build Worker && cd /d %~dp0backend && set PYTHONPATH=%~dp0backend && venv\Scripts\python.exe -m app.worker"

echo [*] Starting Next.js Frontend server...
start "WebToNative - Next.js Frontend" cmd /k "title WebToNative - Next.js Frontend && cd /d %~dp0frontend && npm run dev"

echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 4 >nul

echo [*] Opening WebToNative UI in default browser...
start http://localhost:3000

echo.
echo [OK] FastAPI API Server starting in this window...
echo Press CTRL+C at any time to stop the API server.
echo.

cd /d "%~dp0backend"
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

goto :end

:error
echo.
echo ======================================================================
echo  Startup failed. See error messages above.
echo ======================================================================
pause
exit /b 1

:end
pause
