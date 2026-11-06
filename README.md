# Website-to-APK Builder (V1)

A fast, modular, production-ready system that converts any web application into a signed Android release **APK**, Google Play **AAB**, and a fresh cryptographic keystore.

Includes queueing, worker process isolation, sliding-window rate limiting, SSRF abuse protection, warm Gradle daemon caching, and a responsive single-page web UI.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Frontend (Vanilla JS)     |
                      |   Single-page UI at "/"     |
                      +--------------+--------------+
                                     |
                                     v HTTP / REST
+------------------------------------+------------------------------------+
|                         FastAPI Application                             |
|                                                                         |
|  /api/v1/builds       [POST multipart: URL, App Name, 1:1 Icon]         |
|  /api/v1/builds/{id}  [GET polling status, step, progress, ETA]         |
|  /api/v1/builds/..    [GET downloads: APK, AAB, Full Bundle ZIP]        |
|  /api/v1/health       [GET system queue stats & engine health]          |
|                                                                         |
|  +--------------------+   +-----------------------+   +---------------+ |
|  |  SSRF & IP Guard   |   | SQLite Sliding-Window |   | Auth Hook     | |
|  |  DNS Resolution    |   | Rate Limiter (IP/Hour)|   | anonymous     | |
|  +--------------------+   +-----------------------+   +---------------+ |
+------------------------------------+------------------------------------+
                                     |
                                     v SQLite (WAL mode, ACID)
                      +--------------+--------------+
                      |      Job Queue & DB         |
                      |  Atomic BEGIN IMMEDIATE     |
                      +--------------+--------------+
                                     ^
                                     | Polls & Claims
+------------------------------------+------------------------------------+
|                         Worker Process                                  |
|                                                                         |
|  * Heartbeat loop (recovery.py reaps stuck builds if worker dies)       |
|  * Storage retention cleanup (cleanup.py deletes files after 24h)       |
|  * Max concurrency throttle (MAX_CONCURRENT_BUILDS = 2)                 |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |                         WebViewEngine                             |  |
|  |  1. Isolated temp workspace per build                             |  |
|  |  2. Decodes & generates Android mipmaps + 512x512 with Pillow     |  |
|  |  3. Fresh RSA 2048 keystore per build via keytool                 |  |
|  |  4. Single Gradle pass: assembleRelease + bundleRelease           |  |
|  |  5. apksigner v2 scheme signature verification                    |  |
|  |  6. Bundle packaging (APK + AAB + Keystore + Info + Icon)         |  |
|  |  7. Saves to persistent storage, workspace always deleted         |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## Hard Rules Implemented
1. **No Third-Party APIs or Paid Services**: Pure Android SDK, JDK 17, and open-source Python stack.
2. **Modular Engine Registry**: Engines implement `BuildEngine` ABC. Adding TWA or iOS requires zero changes to core queue or API.
3. **Repository Pattern with SQLAlchemy 2.0**: All queries routed through `BuildRepository` and `RateLimitRepository`. Alembic-ready.
4. **All Config via Environment**: Validated at startup using `pydantic-settings`.
5. **Versioned API**: `/api/v1/...`.
6. **Authentication Hook**: `get_current_user()` dependency returning an anonymous user today with a nullable `user_id` database column.
7. **Zero Password Leakage**: Keystore passwords are never logged or persisted in the database.

---

## Directory Structure

```
├── Dockerfile                   # Multi-stage image with JDK 17, Android SDK & pre-warmed Gradle
├── docker-compose.yml           # Runs api and worker services with shared data volume
├── requirements.txt             # Pinned Python dependencies
├── .env.example                 # Config template
├── frontend/
│   └── index.html               # Single-page UI with live package generator & real-time polling
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & static route serving
│   │   ├── worker.py            # Dedicated background worker process
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings
│   │   │   ├── logging.py       # Structured logger
│   │   │   ├── security.py      # SSRF validation, DNS check, IP blocking
│   │   │   └── ratelimit.py     # Sliding-window rate limiter & abuse guard
│   │   ├── api/
│   │   │   ├── dependencies.py  # Auth hook (anonymous) & IP resolver
│   │   │   └── routes/          # builds.py, downloads.py, engines.py, health.py
│   │   └── modules/
│   │       ├── apk_builder/     # interface.py, manager.py, validators.py
│   │       │   └── webview/     # engine.py (WebViewEngine), cli.py
│   │       ├── job_manager/     # queue.py, recovery.py, cleanup.py
│   │       ├── icon_processor/  # processor.py (Pillow square checks & mipmaps)
│   │       ├── signing/         # keystore.py (keytool wrapper & credentials)
│   │       ├── storage/         # interface.py, local.py (R2 adapter ready)
│   │       └── database/        # engine.py (SQLite WAL), models.py, repositories.py
│   ├── android_templates/
│   │   └── webview/             # Real Gradle Android WebView project
│   ├── blocklist.txt            # Domain phishing/brand abuse blocklist
│   └── tests/                   # Pytest suite (unit, security, queue, integration)
```

---

## Quickstart

### 1. Run with Docker Compose (Recommended)

```bash
docker compose up --build
```
- Open `http://localhost:8000` in your browser.
- Two containers will start:
  - `api`: Handles web traffic and rate limiting.
  - `worker`: Background worker that compiles APKs and bundles.

---

### 2. Run Locally on Host

#### Prerequisites
- Python 3.12+
- JDK 17 (`JAVA_HOME` set)
- Android SDK (`ANDROID_HOME` set with `platform-tools`, `platforms;android-34`, `build-tools;34.0.0`)

#### Installation
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

#### Run CLI Direct Build
```bash
python -m app.modules.apk_builder.webview.cli --url https://example.com --name "My App" --icon ../test_icon.png
```

#### Run Server & Worker (Separate Terminals)
**Terminal 1 (API Server):**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Worker Process):**
```bash
python -m app.worker
```

Visit `http://localhost:8000` to test the complete end-to-end flow.

---

## Running Tests

Run the full unit and security test suite:
```bash
cd backend
python -m pytest tests/ -m "not integration" -v
```

Run the real Android build integration test (`apksigner` validation):
```bash
python -m pytest tests/test_integration.py -v
```

---

## Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/webtoapk.db` | Database connection URL |
| `ANDROID_HOME` | `C:\Android` or `/opt/android-sdk` | Path to Android SDK |
| `JAVA_HOME` | `C:\Program Files\Java\jdk-17` | Path to JDK 17 |
| `DEFAULT_BUILD_ENGINE` | `webview` | Default engine used if none specified |
| `ENABLED_BUILD_ENGINES` | `webview` | Comma-separated enabled engines |
| `MAX_CONCURRENT_BUILDS` | `2` | Max parallel Gradle worker tasks |
| `BUILD_TIMEOUT_SECONDS` | `600` | Process timeout for Gradle executions |
| `WORKER_POLL_INTERVAL_SECONDS` | `0.5` | Polling interval for queued jobs |
| `HEARTBEAT_TIMEOUT_SECONDS` | `120` | Worker crash detection timeout |
| `APK_RETENTION_HOURS` | `24` | Storage retention window before cleanup |
| `RATE_LIMIT_BUILDS_PER_HOUR` | `5` | Sliding window build quota per IP |
| `RATE_LIMIT_STATUS_PER_MINUTE` | `120` | Status/download endpoint rate limit |
| `MAX_QUEUE_LENGTH` | `100` | Global queue limit before rejecting |
| `TRUST_PROXY` | `false` | Whether to trust `X-Forwarded-For` |
| `MAX_ICON_SIZE_MB` | `5` | Maximum icon upload file size |
| `BLOCKLIST_PATH` | `./blocklist.txt` | Path to phishing domain blocklist |
| `ENABLE_BUILD_CACHE` | `true` | Return existing build on matching input hash |

---

## How to Add a New Build Engine (e.g. TWA, iOS, EXE)

1. Create a new folder under `backend/app/modules/apk_builder/<engine_name>/`:
   ```python
   from app.modules.apk_builder.interface import BuildEngine, BuildRequest, BuildResult

   class TwaEngine(BuildEngine):
       @property
       def name(self) -> str:
           return "twa"

       def build(self, request: BuildRequest, progress_callback=None) -> BuildResult:
           # 1. Run bubblewrap CLI or TWA pipeline
           # 2. Return BuildResult(status="completed", apk_path=..., aab_path=...)
   ```
2. Register the engine in `backend/app/main.py` and `backend/app/worker.py`:
   ```python
   from app.modules.apk_builder.twa.engine import TwaEngine
   engine_manager.register(TwaEngine())
   ```
3. Update `.env`:
   ```ini
   ENABLED_BUILD_ENGINES=webview,twa
   ```
   No changes to database schema, job queue, rate limiter, or routes are needed.

---

## Future Roadmap Integration Guide

### 1. Adding User Authentication (Login)
- **Dependency**: In `backend/app/api/dependencies.py`, update `get_current_user()` to decode your JWT or session cookie and return a `User(user_id=decoded_id, role="user")`.
- **Database**: Every row in `build_jobs` already has a nullable `user_id` column.
- **Route**: In `backend/app/api/routes/builds.py`, `current_user.user_id` is automatically linked to the build.

### 2. Adding Payment Gating
- Create `backend/app/modules/billing/`:
  - Hook into `POST /api/v1/builds`: check whether `current_user` has active credits or an active subscription before calling `JobQueue.enqueue`.
  - Add a webhook route `POST /api/v1/webhooks/payment` to increment credits on purchase.

### 3. Switching from SQLite to PostgreSQL
- Update `DATABASE_URL` in `.env`:
  ```ini
  DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/webtoapk
  ```
- All models inherit from SQLAlchemy 2.0 `Base` and contain explicit column lengths and indices, ready for `alembic init` and `alembic revision --autogenerate`.
- `BuildRepository.claim_next_job` automatically uses `FOR UPDATE SKIP LOCKED` when connected to PostgreSQL.

### 4. Switching Local Storage to Cloudflare R2 / AWS S3
- In `backend/app/modules/storage/`, create `r2.py` implementing `StorageInterface`:
  ```python
  class R2Storage(StorageInterface):
      def save_file(self, build_id: str, filename: str, src_path: Path) -> Path:
          # upload to s3/r2 bucket
      def get_file_path(self, build_id: str, filename: str) -> Optional[Path]:
          # generate presigned URL or download to local cache
  ```
- Instantiate `R2Storage` in `main.py` and `worker.py`. The engines, API routes, and workers only communicate with `StorageInterface`.

