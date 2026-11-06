import os
import shutil
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project Directories
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    TEMPLATES_DIR: Path = PROJECT_ROOT / "android_templates"
    STORAGE_DIR: Path = PROJECT_ROOT / "storage_data"
    TEMP_DIR: Path = PROJECT_ROOT / "temp_workspaces"
    DATA_DIR: Path = PROJECT_ROOT / "data"

    # Database
    DATABASE_URL: str = Field(default_factory=lambda: os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'data' / 'webtoapk.db'}"
    ))

    # Android and Java Paths
    ANDROID_HOME: str = os.environ.get("ANDROID_HOME", "C:\\Android")
    JAVA_HOME: str = os.environ.get("JAVA_HOME", "C:\\Program Files\\Java\\jdk-17")
    KEYTOOL_PATH: Optional[str] = None
    APKSIGNER_PATH: Optional[str] = None

    # Build Engines
    DEFAULT_BUILD_ENGINE: str = "webview"
    ENABLED_BUILD_ENGINES: str = "webview"

    # Worker & Build Limits
    MAX_CONCURRENT_BUILDS: int = 2
    BUILD_TIMEOUT_SECONDS: int = 600
    WORKER_POLL_INTERVAL_SECONDS: float = 0.5
    HEARTBEAT_TIMEOUT_SECONDS: int = 120
    APK_RETENTION_HOURS: int = 24

    # Abuse & Rate Limiting
    RATE_LIMIT_BUILDS_PER_HOUR: int = 5
    RATE_LIMIT_STATUS_PER_MINUTE: int = 120
    MAX_QUEUE_LENGTH: int = 100
    TRUST_PROXY: bool = False
    MAX_ICON_SIZE_MB: int = 5
    BLOCKLIST_PATH: Path = PROJECT_ROOT / "blocklist.txt"

    # Caching
    ENABLE_BUILD_CACHE: bool = False

    @property
    def enabled_engines_list(self) -> List[str]:
        return [e.strip().lower() for e in self.ENABLED_BUILD_ENGINES.split(",") if e.strip()]

    def resolve_keytool(self) -> str:
        if self.KEYTOOL_PATH and os.path.exists(self.KEYTOOL_PATH):
            return self.KEYTOOL_PATH
        if self.JAVA_HOME:
            ext = ".exe" if os.name == "nt" else ""
            candidate = os.path.join(self.JAVA_HOME, "bin", f"keytool{ext}")
            if os.path.exists(candidate):
                return candidate
        found = shutil.which("keytool")
        if found:
            return found
        raise RuntimeError(f"keytool not found. Ensure JAVA_HOME is set. Current JAVA_HOME: {self.JAVA_HOME}")

    def resolve_apksigner(self) -> str:
        if self.APKSIGNER_PATH and os.path.exists(self.APKSIGNER_PATH):
            return self.APKSIGNER_PATH
        if self.ANDROID_HOME:
            build_tools_dir = os.path.join(self.ANDROID_HOME, "build-tools")
            if os.path.exists(build_tools_dir):
                # Search available build tool versions descending
                versions = sorted(os.listdir(build_tools_dir), reverse=True)
                for ver in versions:
                    ext = ".bat" if os.name == "nt" else ""
                    candidate = os.path.join(build_tools_dir, ver, f"apksigner{ext}")
                    if os.path.exists(candidate):
                        return candidate
        found = shutil.which("apksigner")
        if found:
            return found
        raise RuntimeError(f"apksigner not found. Ensure ANDROID_HOME is set. Current ANDROID_HOME: {self.ANDROID_HOME}")


settings = Settings()

# Ensure directories exist
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
