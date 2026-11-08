# 📱 WebToAPK - Convert Websites into Native Android Apps

A fast, high-performance, open-source platform to transform any website or web application into signed Android release **APK** & **AAB** packages with custom keystore generation, real-time live preview, Redis job queue, and background worker isolation.

Inspired by clean modern builders like **WebToNative**, built with **Next.js 14**, **FastAPI**, **Redis**, and native **Android Gradle SDK**.

---

## ✨ Features

- **⚡ One-Click Generation:** Transform any responsive website into a production-ready Android App in under 2 minutes.
- **📱 Real-Time Interactive Android Preview:** Seamless live interactive phone mockup displaying the website exactly as it looks when installed on an Android device.
- **🔒 Signed Release APK & Google Play AAB:** Automatically generates unique 2048-bit RSA cryptographic signing keystores and signs packages with `apksigner` (v1 + v2 schemes).
- **🚀 High-Traffic Ready (Redis Queue + Worker):** Built-in Redis queue with atomic job claiming (`BRPOPLPUSH`) and graceful SQLite WAL fallback. Handles high concurrent traffic effortlessly.
- **🛡️ Full In-App Navigation & Cookie Persistence:**
  - Handles internal subdomains, `www` vs non-`www` redirects, and `target="_blank"` / `window.open` inside the app WebView.
  - Persistent third-party cookie handling across page transitions (preserves user login/session state).
  - Hardware back-button navigation (`webView.canGoBack()`).
- **🛡️ Abuse & Security Protection:**
  - SSRF protection (private IP blocking, loopback guard, DNS resolution checks).
  - Sliding-window rate limiting per IP.
  - Phishing and brand domain blocklist verification.
- **📦 Complete Bundle Download:** Download single APK, Google Play AAB, or a full ZIP bundle (APK, AAB, Keystore `.jks`, passwords, SHA-256 fingerprint, and app icon).

---

## 🛠️ Tech Stack

- **Frontend:** Next.js 14 (App Router), React 18, Tailwind CSS, Lucide Icons.
- **Backend API:** Python 3.12, FastAPI, Uvicorn, Pydantic v2.
- **Worker & Queue:** Redis 7 / SQLite WAL fallback, isolated worker subprocesses.
- **Android Toolchain:** JDK 17, Android SDK (API 34), Gradle 8.2, Kotlin 1.9.

---

## 🚀 Quickstart

### Option 1: One-Click Start on Windows (Recommended)

Simply double-click or run:
```cmd
run.bat
```
`run.bat` automatically verifies your environment (Python, Node.js, JDK 17, Android SDK), installs dependencies, starts the FastAPI server, worker process, and Next.js frontend, and opens `http://localhost:3000` in your browser.

---

### Option 2: Docker Compose (All Platforms)

Run everything (Redis, Backend API, Worker) in isolated containers:
```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

### Option 3: Manual Local Setup

#### 1. Backend & Worker Setup
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
cp .env.example .env

# Terminal 1: Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start background build worker
python -m app.worker
```

#### 2. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install packages
npm install

# Start Next.js development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

### Option 4: Direct CLI Build

Build an APK directly from command line without running servers:
```bash
cd backend
python -m app.modules.apk_builder.webview.cli --url "https://yourwebsite.com" --name "My App" --icon "path/to/icon.png"
```

---

## 🧪 Running Tests

Run backend unit, queue, and security test suite:
```bash
cd backend
python -m pytest tests/test_unit_validators_and_icons.py tests/test_phase2_queue.py tests/test_phase3_api_security.py -v
```

---

## ⚙️ Environment Configuration (`.env`)

| Key | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL for queue |
| `QUEUE_BACKEND` | `auto` | `redis`, `sqlite`, or `auto` fallback |
| `DATABASE_URL` | `sqlite:///./data/webtoapk.db` | Database connection URL |
| `ANDROID_HOME` | `C:\Android` or `/opt/android-sdk` | Android SDK path |
| `JAVA_HOME` | `C:\Program Files\Java\jdk-17` | JDK 17 installation path |
| `MAX_CONCURRENT_BUILDS` | `2` | Maximum simultaneous Gradle compilations |
| `RATE_LIMIT_BUILDS_PER_HOUR` | `5` | Build limit per IP per hour |
| `APK_RETENTION_HOURS` | `24` | Auto-cleanup time for generated build files |

---

## 📄 License

This project is licensed under the MIT License.
