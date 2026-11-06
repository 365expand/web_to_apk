from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import builds, downloads, engines, health
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.modules.apk_builder.manager import engine_manager
from app.modules.apk_builder.webview.engine import WebViewEngine
from app.modules.database.engine import Base, engine
from app.modules.storage.local import LocalStorage


# Register default build engines
storage = LocalStorage()
engine_manager.register(WebViewEngine(storage=storage))


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing WebToAPK API server...")

    # Ensure DB tables are initialized
    Base.metadata.create_all(bind=engine)
    logger.info(f"Registered engines: {engine_manager.list_enabled_engines()}")

    yield

    logger.info("Shutting down WebToAPK API server...")


app = FastAPI(
    title="WebToAPK Builder API",
    version="1.0.0",
    description="Production-grade Website to APK & AAB packaging service",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register versioned API v1 routers
app.include_router(builds.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(engines.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

# Serve frontend test UI
frontend_dir = settings.PROJECT_ROOT.parent / "frontend"
frontend_index = frontend_dir / "index.html"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    if frontend_index.exists():
        return FileResponse(str(frontend_index), media_type="text/html")
    return {"message": "WebToAPK API is online. Frontend UI not found."}
